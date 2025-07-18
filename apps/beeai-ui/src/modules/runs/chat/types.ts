/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Role } from '#modules/messages/api/types.ts';
import { UISourcePart } from '#modules/messages/types.ts';

import type { TrajectoryMetadata } from '../api/types';
export interface AgentMessage {
  key: string;
  content: string;
  error?: unknown;
  files?: MessageFile[];
  role: Role.Agent;
  rawContent: string;
  contentTransforms: MessageContentTransform[];
  trajectories?: TrajectoryMetadata[];
}

export interface MessageFile {
  key: string;
  filename: string;
  href: string;
}

export interface MessageContentTransform {
  key: string;
  kind: MessageContentTransformType;
  startIndex: number;
  apply: ({ content, offset }: { content: string; offset: number }) => string;
}

export interface CitationTransform extends MessageContentTransform {
  kind: MessageContentTransformType.Citation;
  sources: UISourcePart[];
}

export enum MessageContentTransformType {
  Citation = 'citation',
  Image = 'image',
}
