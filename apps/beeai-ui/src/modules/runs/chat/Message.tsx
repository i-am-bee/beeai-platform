/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';

import { getErrorMessage } from '#api/utils.ts';
import { ErrorMessage } from '#components/ErrorMessage/ErrorMessage.tsx';
import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import { Spinner } from '#components/Spinner/Spinner.tsx';

import { AgentIcon } from '../components/AgentIcon';
import { useChat } from '../contexts/chat';
import { Role } from '../types';
import classes from './Message.module.scss';
import { type ChatMessage, MessageStatus } from './types';
import { UserIcon } from './UserIcon';

interface Props {
  message: ChatMessage;
}

export function Message({ message }: Props) {
  const { agent } = useChat();
  const { content, role, error } = message;

  const isUserMessage = role === Role.User;
  const isAssistantMessage = role === Role.Assistant;
  const isPending = isAssistantMessage && message.status === MessageStatus.InProgress && !content;
  const isError =
    isAssistantMessage && (message.status === MessageStatus.Failed || message.status === MessageStatus.Aborted);
  const isFailed = isAssistantMessage && message.status === MessageStatus.Failed;

  return (
    <li className={clsx(classes.root)}>
      <div className={classes.sender}>
        <div className={classes.senderIcon}>{isUserMessage ? <UserIcon /> : <AgentIcon />}</div>
        <div className={classes.senderName}>{isUserMessage ? 'User' : agent.name}</div>
      </div>

      <div className={classes.body}>
        {isPending ? (
          <Spinner />
        ) : isError ? (
          <ErrorMessage
            title={isFailed ? 'Failed to generate an assistant message.' : 'Message generation has been cancelled.'}
            subtitle={getErrorMessage(error)}
          />
        ) : (
          <div className={clsx(classes.content, { [classes.isUser]: isUserMessage })}>
            {content ? (
              <MarkdownContent>{content}</MarkdownContent>
            ) : (
              <span className={classes.empty}>Message has no content</span>
            )}
          </div>
        )}
      </div>
    </li>
  );
}
