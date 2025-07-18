/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useAutoScroll } from '#hooks/useAutoScroll.ts';
import { UIAgentMessage } from '#modules/messages/types.ts';
import { checkMessageError, getMessageContent, getMessageSources } from '#modules/messages/utils.ts';

import { AgentOutputBox } from '../components/AgentOutputBox';
import { MessageError } from '../components/MessageError';
import { useAgentRun } from '../contexts/agent-run';
import { MessageFiles } from '../files/components/MessageFiles';
import { MessageSources } from '../sources/components/MessageSources';

interface Props {
  message: UIAgentMessage;
  className?: string;
}

export function HandsOffText({ message, className }: Props) {
  const { agent, isPending } = useAgentRun();

  const content = getMessageContent(message);
  const sources = getMessageSources(message);
  const isError = checkMessageError(message);

  const { ref: autoScrollRef } = useAutoScroll([content]);

  return content || isError ? (
    <div className={className}>
      <AgentOutputBox sources={sources} text={content} isPending={isPending} downloadFileName={`${agent.name}-output`}>
        {isError && <MessageError message={message} />}

        <MessageFiles message={message} />

        <MessageSources message={message} />
      </AgentOutputBox>

      {isPending && <div ref={autoScrollRef} />}
    </div>
  ) : null;
}
