/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import { UIMessage } from '#modules/messages/types.ts';
import { getMessageContent, getMessageSources } from '#modules/messages/utils.ts';

import { useAgentRun } from '../contexts/agent-run';
import classes from './MessageContent.module.scss';

interface Props {
  message: UIMessage;
}

export function MessageContent({ message }: Props) {
  const content = getMessageContent(message);
  const sources = getMessageSources(message);

  const { isPending } = useAgentRun();

  return content ? (
    <MarkdownContent sources={sources} isPending={isPending}>
      {content}
    </MarkdownContent>
  ) : (
    <div className={classes.empty}>Message has no content</div>
  );
}
