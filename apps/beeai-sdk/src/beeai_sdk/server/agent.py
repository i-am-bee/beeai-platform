import asyncio
import inspect
from asyncio import CancelledError, Event
from collections.abc import AsyncGenerator, Callable, Generator
from contextlib import suppress
from typing import NamedTuple, TypeAlias

import janus
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue, QueueManager
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    Message,
    Part,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)

from beeai_sdk.server.context import Context
from beeai_sdk.server.types import RunYield, RunYieldResume
from beeai_sdk.server.utils import cancel_task

AgentFunction: TypeAlias = Callable[[TaskUpdater, RequestContext], AsyncGenerator[RunYield, RunYieldResume]]


class Agent(NamedTuple):
    card: AgentCard
    execute: AgentFunction


def agent(
    name: str | None = None,
    description: str | None = None,
    *,
    additional_interfaces: list[AgentInterface] | None = None,
    capabilities: AgentCapabilities | None = None,
    default_input_modes: list[str] | None = None,
    default_output_modes: list[str] | None = None,
    documentation_url: str | None = None,
    icon_url: str | None = None,
    preferred_transport: str | None = None,
    skills: list[AgentSkill] | None = None,
    version: str | None = None,
) -> Callable[[Callable], Agent]:
    """Decorator to create an agent."""

    def decorator(fn: Callable) -> Agent:
        signature = inspect.signature(fn)
        parameters = list(signature.parameters.values())

        if len(parameters) == 0:
            raise TypeError("The agent function must have at least 'input' argument")
        if len(parameters) > 2:
            raise TypeError("The agent function must have only 'input' and 'context' arguments")
        if len(parameters) == 2 and parameters[1].name != "context":
            raise TypeError("The second argument of the agent function must be 'context'")

        has_context_param = len(parameters) == 2

        resolved_name = name or fn.__name__
        resolved_description = description or fn.__doc__ or ""

        card = AgentCard(
            name=resolved_name,
            description=resolved_description,
            additional_interfaces=additional_interfaces,
            capabilities=capabilities or AgentCapabilities(streaming=True),
            default_input_modes=default_input_modes or ["text"],
            default_output_modes=default_output_modes or ["text"],
            documentation_url=documentation_url,
            icon_url=icon_url,
            preferred_transport=preferred_transport,
            skills=skills
            or [
                AgentSkill(
                    id="default_skill",
                    name=resolved_name,
                    description=resolved_description,
                    tags=["default"],
                )
            ],
            version=version or "1.0.0",
            url="http://localhost:10000",  # dummy url - will be replaced by server
        )

        if inspect.isasyncgenfunction(fn):

            async def execute_fn(message: Message, context: Context) -> None:
                try:
                    gen: AsyncGenerator[RunYield, RunYieldResume] = (
                        fn(message, context) if has_context_param else fn(message)
                    )
                    value = None
                    while True:
                        value = await context.yield_async(await gen.asend(value))
                except StopAsyncIteration:
                    pass
                except Exception as e:
                    await context.yield_async(e)
                finally:
                    context.shutdown()

        elif inspect.iscoroutinefunction(fn):

            async def execute_fn(message: Message, context: Context) -> None:
                try:
                    await context.yield_async(await (fn(message, context) if has_context_param else fn(message)))
                except Exception as e:
                    await context.yield_async(e)
                finally:
                    context.shutdown()

        elif inspect.isgeneratorfunction(fn):

            def _execute_fn_sync(message: Message, context: Context) -> None:
                try:
                    gen: Generator[RunYield, RunYieldResume] = (
                        fn(message, context) if has_context_param else fn(message)
                    )
                    value = None
                    while True:
                        value = context.yield_sync(gen.send(value))
                except StopIteration:
                    pass
                except Exception as e:
                    context.yield_sync(e)
                finally:
                    context.shutdown()

            async def execute_fn(message: Message, context: Context) -> None:
                await asyncio.to_thread(_execute_fn_sync, message, context)

        else:

            def _execute_fn_sync(message: Message, context: Context) -> None:
                try:
                    context.yield_sync(fn(message, context) if has_context_param else fn(message))
                except Exception as e:
                    context.yield_sync(e)
                finally:
                    context.shutdown()

            async def execute_fn(message: Message, context: Context) -> None:
                await asyncio.to_thread(_execute_fn_sync, message, context)

        async def agent_executor(
            task_updater: TaskUpdater, request_context: RequestContext
        ) -> AsyncGenerator[RunYield, RunYieldResume]:
            message = request_context.message
            context = Context(
                configuration=request_context.configuration,
                context_id=request_context.context_id,
                task_id=request_context.task_id,
                task_updater=task_updater,
                current_task=request_context.current_task,
                related_tasks=request_context.related_tasks,
                call_context=request_context.call_context,
            )

            yield_queue = context._yield_queue
            yield_resume_queue = context._yield_resume_queue

            task = asyncio.create_task(execute_fn(message, context))
            try:
                while not task.done() or yield_queue.async_q.qsize() > 0:
                    value = yield await yield_queue.async_q.get()
                    if isinstance(value, Exception):
                        raise value
                    await yield_resume_queue.async_q.put(value)
            except janus.AsyncQueueShutDown:
                pass
            finally:
                await cancel_task(task)

        return Agent(card=card, execute=agent_executor)

    return decorator


class Executor(AgentExecutor):
    def __init__(self, execute_fn: AgentFunction, queue_manager: QueueManager) -> None:
        self._execute_fn = execute_fn
        self._queue_manager = queue_manager
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._cancel_queues: dict[str, EventQueue] = {}

    async def _watch_for_cancellation(self, task_id: str, task: asyncio.Task) -> None:
        cancel_queue = await self._queue_manager.create_or_tap(f"_cancel_{task_id}")
        self._cancel_queues[task_id] = cancel_queue

        try:
            await cancel_queue.dequeue_event()
            cancel_queue.task_done()
            task.cancel()
        finally:
            await cancel_queue.close()
            self._cancel_queues.pop(task_id)

    async def _run_generator(
        self,
        *,
        gen: AsyncGenerator[RunYield, RunYieldResume],
        task_updater: TaskUpdater,
        resume_queue: EventQueue,
    ) -> None:
        cancellation_task = asyncio.create_task(
            self._watch_for_cancellation(task_updater.task_id, asyncio.current_task())
        )

        try:
            await task_updater.start_work()
            value = None
            while True:
                yielded_value = await gen.asend(value)
                match yielded_value:
                    case str(text):
                        await task_updater.update_status(
                            TaskState.working,
                            message=task_updater.new_agent_message(parts=[Part(root=TextPart(text=text))]),
                        )
                    case Part():
                        await task_updater.update_status(
                            TaskState.working,
                            message=task_updater.new_agent_message(parts=[yielded_value]),
                        )
                    case Message(context_id=context_id, task_id=task_id):
                        if context_id != task_updater.context_id or task_id != task_updater.task_id:
                            raise ValueError("Message must have the same context_id and task_id as the task")
                        await task_updater.update_status(TaskState.working, message=yielded_value)
                    case TaskStatus(state=TaskState.input_required, message=message, timestamp=timestamp):
                        await task_updater.requires_input(message=message)
                        value = await resume_queue.dequeue_event()
                        resume_queue.task_done()
                        continue
                    case TaskStatus(state=TaskState.auth_required, message=message, timestamp=timestamp):
                        await task_updater.requires_auth(message=message)
                        value = await resume_queue.dequeue_event()
                        resume_queue.task_done()
                        continue
                    case TaskStatus(state=state, message=message, timestamp=timestamp):
                        await task_updater.update_status(state=state, message=message, timestamp=timestamp)
                value = None
        except StopAsyncIteration:
            await task_updater.complete()
        except CancelledError:
            await task_updater.cancel()
        except Exception as ex:
            await task_updater.failed(task_updater.new_agent_message(parts=[Part(root=TextPart(text=str(ex)))]))
        finally:
            await cancel_task(cancellation_task)

    async def _forward_messages(self, forwarding_started: Event, source_queue: EventQueue, target_queue: EventQueue):
        forwarding_started.set()
        with suppress(CancelledError):
            while True:
                await target_queue.enqueue_event(await source_queue.dequeue_event())
                source_queue.task_done()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        fwd_task = None
        try:
            if context.current_task and context.current_task.status == TaskState.working:
                raise RuntimeError("Cannot resume working task")

            resume_queue = await self._queue_manager.get(task_id=f"_resume_{context.task_id}")
            if not resume_queue:
                resume_queue = await self._queue_manager.create_or_tap(task_id=f"_resume_{context.task_id}")

            long_running_event_queue = await self._queue_manager.create_or_tap(task_id=f"_event_{context.task_id}")

            fwd_started = Event()
            fwd_task = asyncio.create_task(self._forward_messages(fwd_started, long_running_event_queue, event_queue))
            await fwd_started.wait()

            task_updater = TaskUpdater(long_running_event_queue, task_id=context.task_id, context_id=context.context_id)
            if context.current_task and context.current_task.status.state in {
                TaskState.input_required,
                TaskState.auth_required,
            }:
                await resume_queue.enqueue_event(context.message)
            else:
                generator = self._execute_fn(task_updater, context)
                run_generator = self._run_generator(gen=generator, task_updater=task_updater, resume_queue=resume_queue)
                self._running_tasks[context.task_id] = asyncio.create_task(run_generator)
                self._running_tasks[context.task_id].add_done_callback(
                    lambda _: self._running_tasks.pop(context.task_id)
                )

            # Block until asynchronous processing is finished
            _exit_queue = long_running_event_queue.tap()

            while True:
                event = await _exit_queue.dequeue_event()
                _exit_queue.task_done()
                match event:
                    case TaskStatusUpdateEvent(
                        status=TaskStatus(state=TaskState.completed | TaskState.failed | TaskState.canceled)
                    ):
                        await resume_queue.close()
                        await long_running_event_queue.close()
                        break
                    case TaskStatusUpdateEvent(
                        status=TaskStatus(state=TaskState.auth_required | TaskState.input_required)
                    ):
                        break
        finally:
            await cancel_task(fwd_task)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        try:
            if context.current_task and (queue := self._cancel_queues.get(context.task_id)):
                await queue.enqueue_event(context.current_task)
        finally:
            await TaskUpdater(event_queue, task_id=context.task_id, context_id=context.context_id).cancel()
