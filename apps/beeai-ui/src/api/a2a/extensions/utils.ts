/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentExtension } from '@a2a-js/sdk';

import type { A2AComponentExtension, A2AServiceExtension } from './types';

export function extractComponentExtensionData<U extends string, D>(extension: A2AComponentExtension<U, D>) {
  const schema = extension.getMessageSchema();
  const uri = extension.getUri();

  return function (metadata: Record<string, unknown> | undefined) {
    const { success, data: parsed } = schema.safeParse(metadata ?? {});

    if (!success) {
      return undefined;
    }

    return parsed[uri];
  };
}

export function extractServiceExtensionDemands<U extends string, D, F>(extension: A2AServiceExtension<U, D, F>) {
  return function (agentExtensions: AgentExtension[]) {
    const foundExtension = agentExtensions.find(({ uri }) => uri === extension.getUri());
    if (!foundExtension) {
      return null;
    }

    const data = extension.getDemandsSchema().parse(foundExtension.params);
    return data;
  };
}

export function fullfilServiceExtensionDemand<U extends string, D, F>(extension: A2AServiceExtension<U, D, F>) {
  return (metadata: Record<string, unknown>, fullfillment: F) => {
    const fullfilment = extension.getFullfilmentSchema().parse(fullfillment);

    return {
      ...metadata,
      [extension.getUri()]: fullfilment,
    };
  };
}
