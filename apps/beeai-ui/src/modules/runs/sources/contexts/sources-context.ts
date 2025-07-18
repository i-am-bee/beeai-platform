/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import { createContext, type Dispatch, type SetStateAction } from 'react';

import { SourcesData } from '#modules/sources/types.ts';

import type { ActiveSource } from './types';

export const SourcesContext = createContext<SourcesContextValue | undefined>(undefined);

interface SourcesContextValue {
  sourcesData: SourcesData;
  activeSource: ActiveSource | null;
  setActiveSource: Dispatch<SetStateAction<ActiveSource | null>>;
}
