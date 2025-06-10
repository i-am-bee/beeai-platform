/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { MessagePart } from '../api/types';
import type { Role } from '../types';

interface Message {
  key: string;
  role: Role;
  content: string;
  error?: unknown;
}
export interface UserMessage extends Message {
  role: Role.User;
}
export interface AssistantMessage extends Message {
  role: Role.Assistant;
  status: MessageStatus;
}

export type ChatMessage = UserMessage | AssistantMessage;

export type MessageParams = Partial<MessagePart> & { content: string };

export enum MessageStatus {
  InProgress = 'in-progress',
  Completed = 'completed',
  Aborted = 'aborted',
  Failed = 'failed',
}
