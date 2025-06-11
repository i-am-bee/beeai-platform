/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { GenericEvent } from './api/types';

export enum Role {
  User = 'user',
  Assistant = 'assistant',
}

export interface RunStats {
  startTime?: number;
  endTime?: number;
}

export type RunLog = GenericEvent['generic'];
