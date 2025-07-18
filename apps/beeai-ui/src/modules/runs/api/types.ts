/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type TrajectoryMetadata as ApiTrajectoryMetadata } from 'acp-sdk';

export type { CitationMetadata, Message } from 'acp-sdk';

export interface TrajectoryMetadata extends ApiTrajectoryMetadata {
  key?: string;
}

export interface GenericEvent {
  type: 'generic';
  generic: {
    message?: string;
    agent_idx?: number;
  };
}
