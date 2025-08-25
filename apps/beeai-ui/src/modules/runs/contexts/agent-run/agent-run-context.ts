/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';
import { createContext } from 'react';

import type { FormRender } from '#api/a2a/extensions/ui/form.ts';
import type { Agent } from '#modules/agents/api/types.ts';
import type { RunFormValues } from '#modules/form/types.ts';
import type { RunStats } from '#modules/runs/types.ts';

export const AgentRunContext = createContext<AgentRunContextValue | undefined>(undefined);

interface AgentRunContextValue {
  agent: Agent;
  isPending: boolean;
  input?: string;
  stats?: RunStats;
  formRender?: FormRender;
  run: (params: { input?: string; formValues?: RunFormValues }) => Promise<void>;
  cancel: () => void;
  clear: () => void;
}
