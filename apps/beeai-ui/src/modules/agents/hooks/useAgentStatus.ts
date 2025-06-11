/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useProvider } from '#modules/providers/api/queries/useProvider.ts';
import { type Provider, ProviderStatus } from '#modules/providers/api/types.ts';

interface Props {
  providerId: string | null | undefined;
}

function getStatusHelpers(data?: Provider) {
  const status = data?.status;
  const isNotInstalled = status === ProviderStatus.NotInstalled;
  const isInstalling = status === ProviderStatus.Installing;
  const isInstallError = status === ProviderStatus.InstallError;
  const isReady = status === ProviderStatus.Ready;

  return {
    status,
    isNotInstalled,
    isInstalling,
    isInstallError,
    isReady,
  };
}

export function useAgentStatus({ providerId }: Props) {
  const query = useProvider({ id: providerId ?? undefined });

  return {
    refetch: async () => {
      const { data } = await query.refetch();

      return getStatusHelpers(data);
    },
    ...getStatusHelpers(query.data),
  };
}
