/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Artifact, Message } from '@a2a-js/sdk';
import { match } from 'ts-pattern';
import { v4 as uuid } from 'uuid';

import { processMessageMetadata, processParts } from '#api/a2a/part-processors.ts';
import { Role } from '#modules/messages/api/types.ts';
import type { UIAgentMessage, UIUserMessage } from '#modules/messages/types.ts';
import { type UIMessage, UIMessageStatus } from '#modules/messages/types.ts';
import type { ContextHistoryItem } from '#modules/platform-context/api/types.ts';

export function convertHistoryToUIMessages(history: ContextHistoryItem[]): UIMessage[] {
  const messages = history
    .map(({ data }) =>
      match(data)
        .with({ kind: 'message' }, (message: Message) => {
          const metadataParts = processMessageMetadata(message);
          const contentParts = processParts(message.parts);
          const parts = [...metadataParts, ...contentParts];

          return match(message)
            .with({ role: 'agent' }, () => {
              const uiAgentMessage: UIAgentMessage = {
                id: uuid(),
                role: Role.Agent,
                status: UIMessageStatus.Completed,
                taskId: message.taskId,
                parts,
              };

              return uiAgentMessage;
            })
            .with({ role: 'user' }, () => {
              const uIUserMessage: UIUserMessage = {
                id: uuid(),
                role: Role.User,
                taskId: message.taskId,
                parts,
              };

              return uIUserMessage;
            })
            .exhaustive();
        })
        .otherwise((artifact: Artifact) => {
          const contentParts = processParts(artifact.parts);

          const agentMessage: UIAgentMessage = {
            id: uuid(),
            role: Role.Agent,
            status: UIMessageStatus.Completed,
            parts: contentParts,
          };

          return agentMessage;
        }),
    )
    .reduce<UIMessage[]>((messages, message) => {
      const lastMessage = messages.at(-1);
      const shouldGroup = lastMessage && lastMessage.role === message.role && lastMessage.taskId === message.taskId;

      if (shouldGroup) {
        const updatedMessage = {
          ...lastMessage,
          parts: [...lastMessage.parts, ...message.parts],
        };

        return [...messages.slice(0, -1), updatedMessage];
      }

      return [...messages, message];
    }, []);

  return messages;
}
