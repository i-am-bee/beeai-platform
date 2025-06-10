/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { listAgents } from '..';
import { agentKeys } from '../keys';
import type { Agent } from '../types';

export function useListAgents() {
  const query = useQuery({
    queryKey: agentKeys.list(),
    queryFn: listAgents,
    select: (data) => data?.agents as Agent[],
    refetchInterval: 30_000,
  });

  return query;
}
