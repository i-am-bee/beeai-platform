/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { MessagePart } from 'acp-sdk';

export type ComposeMessagePart = MessagePart & { agent_idx: number };
