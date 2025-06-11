/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback, useRef, useState } from 'react';

import { handleStream } from '#api/utils.ts';
import type { Agent } from '#modules/agents/api/types.ts';

import { useCancelRun } from '../api/mutations/useCancelRun';
import { useCreateRunStream } from '../api/mutations/useCreateRunStream';
import type {
  ArtifactEvent,
  GenericEvent,
  MessageCompletedEvent,
  MessagePartEvent,
  RunCancelledEvent,
  RunCompletedEvent,
  RunEvent,
  RunFailedEvent,
  RunId,
  SessionId,
} from '../api/types';
import { EventType } from '../api/types';
import type { MessageParams } from '../chat/types';
import { createMessagePart, createRunStreamRequest } from '../utils';

interface Props {
  onBeforeRun?: () => void;
  onRunFailed?: (event: RunFailedEvent) => void;
  onRunCancelled?: (event: RunCancelledEvent) => void;
  onRunCompleted?: (event: RunCompletedEvent) => void;
  onMessagePart?: (event: ArtifactEvent | MessagePartEvent) => void;
  onMessageCompleted?: (event: MessageCompletedEvent) => void;
  onGeneric?: (event: GenericEvent) => void;
  onDone?: () => void;
  onStop?: () => void;
}

export function useRunAgent({
  onBeforeRun,
  onRunFailed,
  onRunCancelled,
  onRunCompleted,
  onMessagePart,
  onMessageCompleted,
  onGeneric,
  onDone,
  onStop,
}: Props = {}) {
  const abortControllerRef = useRef<AbortController | null>(null);

  const [input, setInput] = useState<string>();
  const [isPending, setIsPending] = useState(false);
  const [runId, setRunId] = useState<RunId>();
  const [sessionId, setSessionId] = useState<SessionId>();

  const { mutateAsync: createRunStream } = useCreateRunStream();
  const { mutate: cancelRun } = useCancelRun();

  const handleDone = useCallback(() => {
    setIsPending(false);

    onDone?.();
  }, [onDone]);

  const runAgent = useCallback(
    async ({ agent, ...params }: { agent: Agent } & MessageParams) => {
      try {
        onBeforeRun?.();

        setIsPending(true);
        setInput(params.content);

        const abortController = new AbortController();
        abortControllerRef.current = abortController;

        const stream = await createRunStream({
          body: createRunStreamRequest({
            agent: agent.name,
            messagePart: createMessagePart(params),
            sessionId,
          }),
          signal: abortController.signal,
        });

        handleStream<RunEvent>({
          stream,
          onEvent: (event) => {
            switch (event.type) {
              case EventType.RunCreated:
                setRunId(event.run.run_id);
                setSessionId(event.run.session_id);

                break;
              case EventType.RunFailed:
                handleDone();
                onRunFailed?.(event);

                break;
              case EventType.RunCancelled:
                handleDone();
                onRunCancelled?.(event);

                break;
              case EventType.RunCompleted:
                handleDone();
                onRunCompleted?.(event);

                break;
              case EventType.MessagePart:
                onMessagePart?.(event);

                break;
              case EventType.MessageCompleted:
                onMessageCompleted?.(event);

                break;
              case EventType.Generic:
                onGeneric?.(event);

                break;
            }
          },
        });
      } catch (error) {
        handleDone();

        throw error;
      }
    },
    [
      sessionId,
      createRunStream,
      handleDone,
      onBeforeRun,
      onRunFailed,
      onRunCancelled,
      onRunCompleted,
      onMessagePart,
      onMessageCompleted,
      onGeneric,
    ],
  );

  const stopAgent = useCallback(() => {
    if (!isPending) {
      return;
    }

    setIsPending(false);

    if (runId) {
      cancelRun({ run_id: runId });
    }

    abortControllerRef.current?.abort();
    abortControllerRef.current = null;

    onStop?.();
  }, [isPending, runId, cancelRun, onStop]);

  const reset = useCallback(() => {
    stopAgent();
    setInput(undefined);
    setRunId(undefined);
    setSessionId(undefined);
  }, [stopAgent]);

  return {
    input,
    isPending,
    runAgent,
    stopAgent,
    reset,
  };
}
