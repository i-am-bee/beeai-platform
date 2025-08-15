/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FormRender } from '#api/a2a/extensions/ui/form.ts';

import type { Role } from './api/types';

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

export type UIMessagePart =
  | UITextPart
  | UIFilePart
  | UIDataPart
  | UISourcePart
  | UITrajectoryPart
  | UIFormPart
  | UITransformPart;

export type UITextPart = {
  kind: UIMessagePartKind.Text;
  id: string;
  text: string;
};

export type UIFilePart = {
  kind: UIMessagePartKind.File;
  id: string;
  url: string;
  filename: string;
  type?: string;
};

export type UISourcePart = {
  kind: UIMessagePartKind.Source;
  id: string;
  url: string;
  messageId: string;
  number: number | null;
  startIndex?: number;
  endIndex?: number;
  title?: string;
  description?: string;
  faviconUrl?: string;
};

export type UITrajectoryPart = {
  kind: UIMessagePartKind.Trajectory;
  id: string;
  title?: string;
  content?: string;
};

// TODO: Temporary for testing purposes
export type UIFormPart = FormRender & {
  kind: UIMessagePartKind.Form;
};

export type UITransformPart = {
  kind: UIMessagePartKind.Transform;
  id: string;
  startIndex: number;
  apply: (content: string, offset: number) => string;
} & (
  | {
      type: UITransformType.Image;
    }
  | {
      type: UITransformType.Source;
      sources: string[];
    }
);

export type UIDataPart = {
  kind: UIMessagePartKind.Data;
  data: Record<string, unknown>;
};

export enum UIMessagePartKind {
  Text = 'text',
  File = 'file',
  Data = 'data',
  Source = 'source',
  Trajectory = 'trajectory',
  Form = 'form',
  Transform = 'transform',
}

export enum UIMessageStatus {
  InProgress = 'in-progress',
  Completed = 'completed',
  Aborted = 'aborted',
  Failed = 'failed',
}

export enum UITransformType {
  Source = 'source',
  Image = 'image',
}

export enum UIFormType {
  Render = 'render',
  Response = 'response',
}
