/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { UISourcePart } from '#modules/messages/types.ts';

export interface SourcesData {
  [messageKey: string]: UISourcePart[];
}
