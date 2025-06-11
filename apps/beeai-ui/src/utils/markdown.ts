/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export function createCodeBlock(language: string, snippet: string) {
  return `\`\`\`${language}\n${snippet}\n\`\`\``;
}
