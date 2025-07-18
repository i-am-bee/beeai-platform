/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Role } from './api/types';
import { UIAgentMessage, UIMessage, UIMessagePartKind, UIMessageStatus, UIUserMessage } from './types';

export function isUserMessage(message: UIMessage): message is UIUserMessage {
  return message.role === Role.User;
}

export function isAgentMessage(message: UIMessage): message is UIAgentMessage {
  return message.role === Role.Agent;
}

export function getMessageContent(message: UIMessage) {
  const content = message.parts.reduce(
    (text, part) => (part.kind === UIMessagePartKind.Text ? text.concat(part.text) : text),
    '',
  );

  return content;
}

export function getMessageFiles(message: UIMessage) {
  const files = message.parts.filter((part) => part.kind === UIMessagePartKind.File);

  return files;
}

export function getMessageSources(message: UIMessage) {
  const sources = message.parts.filter((part) => part.kind === UIMessagePartKind.Source);

  return sources;
}

export function getMessageTrajectories(message: UIMessage) {
  const trajectories = message.parts.filter((part) => part.kind === UIMessagePartKind.Trajectory);

  return trajectories;
}

export function checkMessageError(message: UIAgentMessage) {
  const { status } = message;
  const isError = status === UIMessageStatus.Failed || status === UIMessageStatus.Aborted;

  return isError;
}
