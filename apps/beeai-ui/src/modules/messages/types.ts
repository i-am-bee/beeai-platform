/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Role } from './api/types';

export interface UIMessage {
  id: string;
  role: Role;
  parts: UIMessagePart[];
  error?: Error;
}

export interface UIUserMessage extends UIMessage {
  role: Role.User;
}

export interface UIAgentMessage extends UIMessage {
  role: Role.Agent;
  status: UIMessageStatus;
}

export type UIMessagePart = UITextPart | UIFilePart | UISourcePart | UITrajectoryPart;

export type UITextPart = {
  kind: UIMessagePartKind.Text;
  text: string;
};

export type UIFilePart = {
  kind: UIMessagePartKind.File;
  id: string;
  filename: string;
  url: string;
};

export type UISourcePart = {
  kind: UIMessagePartKind.Source;
  id: string;
  url: string;
  messageId: string;
  number: number;
  startIndex: number;
  endIndex: number;
  title?: string;
  description?: string;
  faviconUrl?: string;
};

export type UITrajectoryPart = {
  kind: UIMessagePartKind.Trajectory;
  id: string;
  message?: string;
  toolName?: string;
};

export enum UIMessagePartKind {
  Text = 'text',
  File = 'file',
  Source = 'source',
  Trajectory = 'trajectory',
}

export enum UIMessageStatus {
  InProgress = 'in-progress',
  Completed = 'completed',
  Aborted = 'aborted',
  Failed = 'failed',
}
