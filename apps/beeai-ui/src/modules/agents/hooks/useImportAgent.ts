/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback, useEffect, useMemo, useState } from 'react';

import { useCreateProviderBuild } from '#modules/provider-builds/api/mutations/useCreateProviderBuild.ts';
import { useProviderBuild } from '#modules/provider-builds/api/queries/useProviderBuild.ts';
import { useProviderBuildLogs } from '#modules/provider-builds/api/queries/useProviderBuildLogs.ts';
import { useImportProvider } from '#modules/providers/api/mutations/useImportProvider.ts';
import type { Provider } from '#modules/providers/api/types.ts';
import { ProviderSourcePrefixes } from '#modules/providers/constants.ts';
import { ProviderSource } from '#modules/providers/types.ts';
import { maybeParseJson } from '#modules/runs/utils.ts';
import { isNotNull } from '#utils/helpers.ts';

import { useAgent } from '../api/queries/useAgent';
import type { ImportAgentFormValues } from '../types';

export function useImportAgent() {
  const [buildId, setBuildId] = useState<string>();
  const [provider, setProvider] = useState<Provider>();

  const { data: build } = useProviderBuild({ id: buildId });
  const { data: buildLogs } = useProviderBuildLogs({ id: buildId });
  const { data: agent } = useAgent({ providerId: provider?.id });

  const buildStatus = build?.status;
  const buildDestination = build?.destination;

  const {
    mutateAsync: createProviderBuild,
    isPending: isCreateBuildPending,
    error: buildError,
  } = useCreateProviderBuild();

  const {
    mutateAsync: importProvider,
    isPending: isImportPending,
    error: importError,
  } = useImportProvider({ onSuccess: setProvider });

  const logs = useMemo(
    () =>
      buildLogs
        ?.map(({ data }) => {
          const parsed = maybeParseJson(data);

          if (!parsed) {
            return null;
          }

          const { type, value } = parsed;

          if (type === 'json') {
            const json = JSON.parse(value);
            const message = json.message;

            if (message && typeof message === 'string') {
              return message;
            }
          }

          return value;
        })
        .filter(isNotNull) ?? [],
    [buildLogs],
  );

  const isBuildPending = useMemo(
    () => isCreateBuildPending || (buildId && buildStatus !== 'completed' && buildStatus !== 'failed'),
    [isCreateBuildPending, buildId, buildStatus],
  );

  const isPending = useMemo(
    () => isImportPending || isBuildPending || (provider && !agent),
    [isImportPending, isBuildPending, provider, agent],
  );

  const error = useMemo(() => getProviderError({ buildError, importError }), [buildError, importError]);

  const importAgent = useCallback(
    async ({ source, location }: ImportAgentFormValues) => {
      if (source === ProviderSource.GitHub) {
        const createdBuild = await createProviderBuild({ location });

        setBuildId(createdBuild?.id);
      } else if (source === ProviderSource.Docker) {
        await importProvider({ location: `${ProviderSourcePrefixes[source]}${location}` });
      }
    },
    [createProviderBuild, importProvider],
  );

  useEffect(() => {
    if (buildStatus === 'completed' && buildDestination) {
      importProvider({ location: buildDestination });
    }
  }, [buildStatus, buildDestination, importProvider]);

  return {
    agent,
    logs,
    isPending,
    error,
    importAgent,
  };
}

function getProviderError({ buildError, importError }: { buildError: Error | null; importError: Error | null }) {
  if (buildError) {
    return {
      title: 'Failed to build provider',
      message: buildError.message,
    };
  } else if (importError) {
    return {
      title: 'Failed to import provider',
      message: importError.message,
    };
  }

  return null;
}
