/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { type PropsWithChildren, useCallback, useMemo, useRef, useState } from 'react';
import { v4 as uuid } from 'uuid';

import { buildA2AClient } from '#api/a2a/client.ts';
import { type ChatRun, RunResultType } from '#api/a2a/types.ts';
import { createTextPart } from '#api/a2a/utils.ts';
import { getErrorCode } from '#api/utils.ts';
import { useHandleError } from '#hooks/useHandleError.ts';
import { useImmerWithGetter } from '#hooks/useImmerWithGetter.ts';
import type { Agent } from '#modules/agents/api/types.ts';
import { FileUploadProvider } from '#modules/files/contexts/FileUploadProvider.tsx';
import { useFileUpload } from '#modules/files/contexts/index.ts';
import { convertFilesToUIFileParts } from '#modules/files/utils.ts';
import { Role } from '#modules/messages/api/types.ts';
import type { UIAgentMessage, UIMessageForm, UITask, UIUserMessage } from '#modules/messages/types.ts';
import { UIMessagePartKind, UIMessageStatus } from '#modules/messages/types.ts';
import { addTranformedMessagePart, isAgentMessage } from '#modules/messages/utils.ts';
import { usePlatformContext } from '#modules/platform-context/contexts/index.ts';
import { PlatformContextProvider } from '#modules/platform-context/contexts/PlatformContextProvider.tsx';
import type { RunStats } from '#modules/runs/types.ts';
import { SourcesProvider } from '#modules/sources/contexts/SourcesProvider.tsx';
import { getTaskSourcesMap } from '#modules/sources/utils.ts';
import type { TaskId } from '#modules/tasks/api/types.ts';
import { isNotNull } from '#utils/helpers.ts';

import { TasksProvider } from '../../../tasks/contexts/tasks-context/TasksProvider';
import { AgentStatusProvider } from '../agent-status/AgentStatusProvider';
import { AgentRunContext } from './agent-run-context';

interface Props {
  agent: Agent;
}

export function AgentRunProviders({ agent, children }: PropsWithChildren<Props>) {
  return (
    <PlatformContextProvider>
      <FileUploadProvider allowedContentTypes={agent.defaultInputModes}>
        <AgentRunProvider agent={agent}>{children}</AgentRunProvider>
      </FileUploadProvider>
    </PlatformContextProvider>
  );
}

function AgentRunProvider({ agent, children }: PropsWithChildren<Props>) {
  const { getContextId, resetContext, getFullfilments } = usePlatformContext();
  const [tasks, getTasks, setTasks] = useImmerWithGetter<UITask[]>([]);
  const [input, setInput] = useState<string>();
  const [isPending, setIsPending] = useState(false);
  const [stats, setStats] = useState<RunStats>();

  const pendingSubscription = useRef<() => void>(undefined);
  const pendingRun = useRef<ChatRun>(undefined);

  const errorHandler = useHandleError();

  const a2aAgentClient = useMemo(
    () =>
      buildA2AClient({
        providerId: agent.provider.id,
        extensions: agent.capabilities.extensions ?? [],
      }),
    [agent.provider.id, agent.capabilities.extensions],
  );
  const { files, clearFiles } = useFileUpload();

  const updateCurrentAgentMessage = useCallback(
    (updater: (message: UIAgentMessage) => void) => {
      setTasks((tasks) => {
        const taskId = pendingRun.current?.taskId;
        const task = taskId ? tasks.find(({ id }) => id === taskId) : tasks.at(-1);
        const lastMessage = task?.messages.at(-1);

        if (lastMessage && isAgentMessage(lastMessage)) {
          updater(lastMessage);
        } else {
          throw new Error('There is no last agent message.');
        }
      });
    },
    [setTasks],
  );

  const updateCurrentTask = useCallback(
    (updater: (task: UITask) => void) => {
      setTasks((tasks) => {
        const taskId = pendingRun.current?.taskId;
        const task = taskId ? tasks?.find((task) => taskId === task.id) : tasks.at(-1);

        if (task) {
          updater(task);
        } else {
          throw new Error('Task not found.');
        }
      });
    },
    [setTasks],
  );

  const handleError = useCallback(
    (error: unknown) => {
      const errorCode = getErrorCode(error);

      errorHandler(error, {
        errorToast: { title: errorCode?.toString() ?? 'Failed to run agent.', includeErrorMessage: true },
      });

      if (error instanceof Error) {
        updateCurrentAgentMessage((message) => {
          message.error = error;
          message.status = UIMessageStatus.Failed;
        });
      }
    },
    [errorHandler, updateCurrentAgentMessage],
  );

  const cancel = useCallback(async () => {
    if (pendingRun.current && pendingSubscription.current) {
      updateCurrentTask((task) => {
        task.status.state = 'canceled';
      });
      updateCurrentAgentMessage((message) => {
        message.status = UIMessageStatus.Aborted;
      });

      pendingSubscription.current();
      await pendingRun.current.cancel();
    } else {
      throw new Error('No run in progress');
    }
  }, [updateCurrentAgentMessage, updateCurrentTask]);

  const clear = useCallback(() => {
    setTasks([]);
    setStats(undefined);
    clearFiles();
    resetContext();
    setIsPending(false);
    setInput(undefined);
    pendingRun.current = undefined;
  }, [setTasks, clearFiles, resetContext]);

  const checkPendingRun = useCallback(() => {
    if (pendingRun.current || pendingSubscription.current) {
      throw new Error('A run is already in progress');
    }
  }, []);

  const run = useCallback(
    async (message: UIUserMessage, taskId?: TaskId) => {
      checkPendingRun();

      const contextId = getContextId();

      setIsPending(true);
      setStats({ startTime: Date.now() });

      const fulfillments = await getFullfilments();

      const agentMessage: UIAgentMessage = {
        id: uuid(),
        role: Role.Agent,
        parts: [],
        status: UIMessageStatus.InProgress,
      };

      setTasks((tasks) => {
        if (taskId) {
          const task = tasks.find(({ id }) => id === taskId);
          if (!task) {
            throw new Error('The task was not found');
          }

          task.messages.push(message, agentMessage);
        } else {
          const task: UITask = {
            id: uuid(),
            messages: [message, agentMessage],
            contextId,
            kind: 'task',
            status: { state: 'unknown' },
          };
          tasks.push(task);
        }
      });

      try {
        const run = a2aAgentClient.chat({
          message,
          contextId,
          fulfillments,
          taskId,
        });
        pendingRun.current = run;

        pendingSubscription.current = run.subscribe(({ parts, taskId: responseTaskId }) => {
          if (pendingRun.current && !pendingRun.current.taskId) {
            updateCurrentTask((task) => {
              task.id = responseTaskId;
            });
            pendingRun.current.taskId = responseTaskId;
          }

          parts.forEach((part) => {
            updateCurrentAgentMessage((message) => {
              const updatedParts = addTranformedMessagePart(part, message);
              message.parts = updatedParts;
            });
          });
        });

        const result = await run.done;
        if (result && result.type === RunResultType.FormRequired) {
          updateCurrentTask((task) => {
            task.status.state = 'input-required';
          });
          updateCurrentAgentMessage((message) => {
            message.parts.push({ kind: UIMessagePartKind.Form, ...result.form });
          });
        } else {
          updateCurrentTask((task) => {
            task.status.state = 'completed';
          });
          updateCurrentAgentMessage((message) => {
            message.status = UIMessageStatus.Completed;
          });
        }
      } catch (error) {
        handleError(error);
      } finally {
        setIsPending(false);
        setStats((stats) => ({ ...stats, endTime: Date.now() }));
        pendingRun.current = undefined;
        pendingSubscription.current = undefined;
      }
    },
    [
      checkPendingRun,
      getContextId,
      getFullfilments,
      setTasks,
      a2aAgentClient,
      updateCurrentTask,
      updateCurrentAgentMessage,
      handleError,
    ],
  );

  const chat = useCallback(
    (input: string) => {
      checkPendingRun();

      setInput(input);

      const message: UIUserMessage = {
        id: uuid(),
        role: Role.User,
        parts: [createTextPart(input), ...convertFilesToUIFileParts(files)].filter(isNotNull),
      };

      clearFiles();

      return run(message);
    },
    [checkPendingRun, clearFiles, files, run],
  );

  const submitForm = useCallback(
    (form: UIMessageForm, taskId?: TaskId) => {
      checkPendingRun();

      const message: UIUserMessage = {
        id: uuid(),
        role: Role.User,
        parts: [],
        form,
      };

      return run(message, taskId);
    },
    [checkPendingRun, run],
  );

  const sources = useMemo(() => getTaskSourcesMap(tasks), [tasks]);

  const contextValue = useMemo(() => {
    return {
      agent,
      isPending,
      input,
      stats,
      chat,
      submitForm,
      cancel,
      clear,
    };
  }, [agent, isPending, input, stats, chat, submitForm, cancel, clear]);

  return (
    <AgentStatusProvider agent={agent} isMonitorStatusEnabled>
      <SourcesProvider sources={sources}>
        <TasksProvider tasks={getTasks()}>
          <AgentRunContext.Provider value={contextValue}>{children}</AgentRunContext.Provider>
        </TasksProvider>
      </SourcesProvider>
    </AgentStatusProvider>
  );
}
