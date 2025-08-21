/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type PropsWithChildren, useCallback, useEffect, useState } from 'react';

import { mcpExtension } from '#api/a2a/extensions/services/mcp.ts';
import { extractServiceExtensionDemands } from '#api/a2a/extensions/utils.ts';
import { useApp } from '#contexts/App/index.ts';
import type { Agent } from '#modules/agents/api/types.ts';

import { useCreateContext } from '../api/mutations/useCreateContext';
import { useCreateContextToken } from '../api/mutations/useCreateContextToken';
import { buildFullfilments } from './build-fulfillments';
import { PlatformContext } from './platform-context';

const mcpExtensionExtractor = extractServiceExtensionDemands(mcpExtension);

export function PlatformContextProvider({ children, agent }: PropsWithChildren<{ agent: Agent | null }>) {
  const mcpDemands = mcpExtensionExtractor(agent?.capabilities.extensions ?? []);
  const { featureFlags } = useApp();
  const [contextId, setContextId] = useState<string | null>(null);
  const { mutateAsync: createContext } = useCreateContext();
  const { mutateAsync: createContextToken } = useCreateContextToken();
  const [selectedMCPServers, setSelectedMCPServers] = useState<Record<string, string>>(
    Object.keys(mcpDemands?.mcp_demands ?? {}).reduce((memo, value) => {
      memo[value] = '';
      return memo;
    }, {}),
  );

  const setContext = useCallback(
    (context: Awaited<ReturnType<typeof createContext>>) => {
      if (!context) {
        throw new Error(`Context has not been created`);
      }

      setContextId(context.id);
    },
    [setContextId],
  );

  const resetContext = useCallback(() => {
    setContextId(null);

    createContext().then(setContext);
  }, [createContext, setContext]);

  const selectMCPServer = useCallback(
    (key: string, value: string) => {
      setSelectedMCPServers((prev) => ({ ...prev, [key]: value }));
    },
    [setSelectedMCPServers],
  );

  const getPlatformToken = useCallback(async () => {
    if (contextId === null) {
      throw new Error('Illegal State - Context ID is not set.');
    }

    const contextToken = await createContextToken({
      contextId,
      globalPermissionGrant: {
        llm: ['*'],
        a2a_proxy: [],
        contexts: [],
        embeddings: ['*'],
        feedback: [],
        files: [],
        providers: [],
        variables: [],
        vector_stores: [],
      },
      contextPermissionGrant: {
        files: ['*'],
        vector_stores: ['*'],
      },
    });

    if (!contextToken) {
      throw new Error('Could not generate context token');
    }

    return contextToken.token;
  }, [contextId, createContextToken]);

  const getFullfilments = useCallback(async () => {
    const platformToken = await getPlatformToken();
    return buildFullfilments({ platformToken, selectedMCPServers, featureFlags });
  }, [getPlatformToken, featureFlags, selectedMCPServers]);

  useEffect(() => {
    createContext().then(setContext);
  }, [createContext, setContext]);

  const getContextId = useCallback(() => {
    if (!contextId) {
      throw new Error('Context ID is not set');
    }

    return contextId;
  }, [contextId]);

  return (
    <PlatformContext.Provider
      value={{
        contextId,
        getContextId,
        resetContext,
        getPlatformToken,
        getFullfilments,
        selectMCPServer,
        selectedMCPServers,
      }}
    >
      {children}
    </PlatformContext.Provider>
  );
}
