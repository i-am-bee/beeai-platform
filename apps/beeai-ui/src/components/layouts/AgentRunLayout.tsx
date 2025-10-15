/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import { AgentHeader } from '#modules/agents/components/detail/AgentHeader.tsx';

import classes from './AgentRunLayout.module.scss';

export function AgentRunLayout({ children }: PropsWithChildren) {
  return (
    <div className={classes.root}>
      <AgentHeader />

      {children}
    </div>
  );
}
