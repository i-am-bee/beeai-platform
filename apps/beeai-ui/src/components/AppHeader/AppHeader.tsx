/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { useParams } from 'react-router';

import { MainNav } from '#components/layouts/MainNav.tsx';
import { useAgent } from '#modules/agents/api/queries/useAgent.ts';
import type { AgentPageParams } from '#modules/agents/types.ts';
import { getAgentDisplayName } from '#modules/agents/utils.ts';
import { NAV } from '#utils/vite-constants.ts';

import { Container } from '../layouts/Container';
import { AgentDetailButton } from './AgentDetailButton';
import classes from './AppHeader.module.scss';
import { AppHeaderNav } from './AppHeaderNav';

interface Props {
  className?: string;
}

export function AppHeader({ className }: Props) {
  const { agentName } = useParams<AgentPageParams>();
  const { data: agent } = useAgent({ name: agentName ?? '' });

  return (
    <header className={clsx(classes.root, className)}>
      <Container size="full">
        <div className={clsx(classes.holder, { [classes.hasNav]: NAV.length > 0 })}>
          <MainNav />

          {NAV.length > 0 && <AppHeaderNav items={NAV} />}

          {!NAV.length && agent && (
            <>
              <p className={classes.agentName}>{getAgentDisplayName(agent)}</p>

              <div className={classes.agentDetailButtonContainer}>
                <AgentDetailButton />
              </div>
            </>
          )}
        </div>
      </Container>
    </header>
  );
}
