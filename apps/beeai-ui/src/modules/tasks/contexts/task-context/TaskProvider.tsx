/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import type { TaskContextValue } from './task-context';
import { TaskContext } from './task-context';

export function TaskProvider({ task, children }: PropsWithChildren<TaskContextValue>) {
  return <TaskContext.Provider value={{ task }}>{children}</TaskContext.Provider>;
}
