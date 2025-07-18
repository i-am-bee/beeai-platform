/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { v4 as uuid } from 'uuid';

import { UIAgentMessage, UIMessage, UIMessagePartKind, UISourcePart } from '#modules/messages/types.ts';
import { getMessageSources } from '#modules/messages/utils.ts';
import { SourcesData } from '#modules/sources/types.ts';

import type { CitationMetadata } from '../api/types';

export function prepareMessageSources({ message, metadata }: { message: UIAgentMessage; metadata: CitationMetadata }) {
  const { url, start_index, end_index, title, description } = metadata;
  const prevSources = getMessageSources(message);

  if (url == null || start_index == null || end_index == null) {
    return { sources: prevSources, newSource: undefined };
  }

  const id = uuid();

  const sources: UISourcePart[] = [
    ...prevSources,
    {
      kind: UIMessagePartKind.Source as const,
      id,
      url,
      messageId: message.id,
      startIndex: start_index,
      endIndex: end_index,
      title: title ?? undefined,
      description: description ?? undefined,
    },
  ]
    .sort((a, b) => a.startIndex - b.startIndex)
    .map((source, idx) => ({
      ...source,
      number: idx + 1,
    }));

  const newSource = sources.find((source) => source.id === id);

  return { sources, newSource };
}

export function extractSources(messages: UIMessage[]) {
  const sources = messages.reduce<SourcesData>(
    (data, message) => ({
      ...data,
      [message.id]: getMessageSources(message),
    }),
    {},
  );

  return sources;
}
