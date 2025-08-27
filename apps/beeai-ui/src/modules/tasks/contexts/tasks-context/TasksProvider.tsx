/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import type { TasksContextValue } from './tasks-context';
import { TasksContext } from './tasks-context';

export function TasksProvider({ tasks, children }: PropsWithChildren<TasksContextValue>) {
  return <TasksContext.Provider value={{ tasks }}>{children}</TasksContext.Provider>;
}
