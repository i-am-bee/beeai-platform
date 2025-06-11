/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';
import { useMemo, useState } from 'react';

import { AppContext } from './app-context';

export function AppProvider({ children }: PropsWithChildren) {
  const [navigationOpen, setNavigationOpen] = useState(false);
  const [agentDetailOpen, setAgentDetailOpen] = useState(false);
  const [closeNavOnClickOutside, setCloseNavOnClickOutside] = useState(false);

  const contextValue = useMemo(
    () => ({
      navigationOpen,
      agentDetailOpen,
      closeNavOnClickOutside,
      setNavigationOpen,
      setAgentDetailOpen,
      setCloseNavOnClickOutside,
    }),
    [navigationOpen, agentDetailOpen, closeNavOnClickOutside],
  );

  return <AppContext.Provider value={contextValue}>{children}</AppContext.Provider>;
}
