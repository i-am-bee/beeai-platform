/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useState } from 'react';

import { useToast } from '#contexts/Toast/index.ts';
import { TaskType, useTasks } from '#hooks/useTasks.ts';
import { agentKeys } from '#modules/agents/api/keys.ts';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { useAgentStatus } from '#modules/agents/hooks/useAgentStatus.ts';

interface Props {
  id?: string;
}

export function useMonitorProvider({ id }: Props) {
  const [isDone, setIsDone] = useState(false);
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  const { addTask, removeTask } = useTasks();

  const { refetch: refetchStatus } = useAgentStatus({ providerId: id });
  const { data: agents } = useListAgents();

  const checkProvider = useCallback(async () => {
    const { isReady, isInstallError } = await refetchStatus();

    if (isReady) {
      agents?.forEach(({ name }) => {
        addToast({
          title: `${name} has installed successfully.`,
          kind: 'info',
          timeout: 5_000,
        });
      });
    } else if (isInstallError) {
      agents?.forEach(({ name }) => {
        addToast({
          title: `${name} failed to install.`,
          timeout: 5_000,
        });
      });
    }

    if (isReady || isInstallError) {
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });

      if (id) {
        removeTask({ id, type: TaskType.ProviderStatusCheck });
      }

      setIsDone(true);
    }
  }, [id, agents, queryClient, refetchStatus, addToast, removeTask]);

  useEffect(() => {
    if (id && !isDone) {
      addTask({
        id,
        type: TaskType.ProviderStatusCheck,
        task: checkProvider,
        delay: CHECK_PROVIDER_STATUS_INTERVAL,
      });

      return () => {
        removeTask({ id, type: TaskType.ProviderStatusCheck });
      };
    }
  }, [id, isDone, addTask, removeTask, checkProvider]);
}

const CHECK_PROVIDER_STATUS_INTERVAL = 2000;
