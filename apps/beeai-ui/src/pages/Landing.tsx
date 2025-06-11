/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Loading } from '@carbon/react';
import { useEffect } from 'react';

import { useViewTransition } from '#hooks/useViewTransition.ts';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { routes } from '#utils/router.ts';

import classes from './Landing.module.scss';

export function Landing() {
  const { data: agents } = useListAgents();
  const { transitionTo } = useViewTransition();

  useEffect(() => {
    const firstAgent = agents?.at(0);
    if (firstAgent) {
      transitionTo(routes.agentRun({ name: firstAgent.name }));
    }
  }, [agents, transitionTo]);

  return (
    <div className={classes.root}>
      <Loading withOverlay={false} />
    </div>
  );
}
