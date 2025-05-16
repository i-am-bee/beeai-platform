/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import type { PropsWithChildren } from 'react';
import { useCallback, useMemo, useState } from 'react';

import { AppContext } from './app-context';

export function AppProvider({ children }: PropsWithChildren) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [agentDetailOpen, setAgentDetailOpen] = useState(false);

  const toggleSidebar = useCallback(() => {
    setSidebarOpen((state) => !state);
  }, []);

  const toggleAgentDetail = useCallback(() => {
    setAgentDetailOpen((state) => !state);
  }, []);

  const contextValue = useMemo(
    () => ({ sidebarOpen, agentDetailOpen, toggleSidebar, toggleAgentDetail }),
    [sidebarOpen, agentDetailOpen, toggleSidebar, toggleAgentDetail],
  );

  return <AppContext.Provider value={contextValue}>{children}</AppContext.Provider>;
}
