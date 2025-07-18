/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { FilePart, Part } from '@a2a-js/sdk';
import humanizeDuration from 'humanize-duration';
import JSON5 from 'json5';
import { v4 as uuid } from 'uuid';

import { UISourcePart } from '#modules/messages/types.ts';
import { isNotNull } from '#utils/helpers.ts';
import { toMarkdownCitation, toMarkdownImage } from '#utils/markdown.ts';

import { type CitationTransform, type MessageContentTransform, MessageContentTransformType } from './chat/types';
import type { UploadFileResponse } from './files/api/types';
import type { FileEntity } from './files/types';
import { getFileContentUrl } from './files/utils';

humanizeDuration.languages.shortEn = {
  h: () => 'h',
  m: () => 'min',
  s: () => 's',
};

export function runDuration(ms: number) {
  const duration = humanizeDuration(ms, {
    units: ['h', 'm', 's'],
    round: true,
    delimiter: ' ',
    spacer: '',
    language: 'shortEn',
  });

  return duration;
}

export function createFileParts(files: (UploadFileResponse & { type: string })[]): FilePart[] {
  const messageParts: FilePart[] = files.map(({ id, filename, type }) => ({
    kind: 'file',
    file: {
      uri: getFileContentUrl({ id, addBase: true }),
      name: filename,
      mimeType: type,
    },
  }));

  return messageParts;
}

export function createImageTransform({
  imageUrl,
  insertAt,
}: {
  imageUrl: string;
  insertAt: number;
}): MessageContentTransform {
  const startIndex = insertAt;

  return {
    key: uuid(),
    kind: MessageContentTransformType.Image,
    startIndex,
    apply: ({ content, offset }) => {
      const adjustedStartIndex = startIndex + offset;
      const before = content.slice(0, adjustedStartIndex);
      const after = content.slice(adjustedStartIndex);

      return `${before}${toMarkdownImage(imageUrl)}${after}`;
    },
  };
}

export function createCitationTransform({ source }: { source: UISourcePart }): CitationTransform {
  const { startIndex, endIndex } = source;

  return {
    key: uuid(),
    kind: MessageContentTransformType.Citation,
    startIndex,
    sources: [source],
    apply: function ({ content, offset }) {
      const adjustedStartIndex = startIndex + offset;
      const adjustedEndIndex = endIndex + offset;
      const before = content.slice(0, adjustedStartIndex);
      const text = content.slice(adjustedStartIndex, adjustedEndIndex);
      const after = content.slice(adjustedEndIndex);

      return `${before}${toMarkdownCitation({ text, sources: this.sources })}${after}`;
    },
  };
}

export function applyContentTransforms({
  rawContent,
  transforms,
}: {
  rawContent: string;
  transforms: MessageContentTransform[];
}): string {
  let offset = 0;

  const transformedContent = transforms
    .sort((a, b) => a.startIndex - b.startIndex)
    .reduce((content, transform) => {
      const newContent = transform.apply({ content, offset });
      offset += newContent.length - content.length;

      return newContent;
    }, rawContent);

  return transformedContent;
}

export function extractValidUploadFiles(files: FileEntity[]) {
  const uploadFiles = files
    .map(({ uploadFile, originalFile: { type } }) => (uploadFile ? { ...uploadFile, type } : null))
    .filter(isNotNull);

  return uploadFiles;
}

export function mapToMessageFiles(uploadFiles: UploadFileResponse[]) {
  return uploadFiles.map(({ id, filename }) => ({ key: id, filename, href: getFileContentUrl({ id }) }));
}

export const parseJsonLikeString = (string: string): unknown | string => {
  try {
    const json = JSON5.parse(string);

    return json;
  } catch {
    return string;
  }
};

export function extractTextFromParts(parts: Part[]): string {
  const text = parts
    .filter((part) => part.kind === 'text')
    .map((part) => part.text)
    .join('\n');

  return text;
}
