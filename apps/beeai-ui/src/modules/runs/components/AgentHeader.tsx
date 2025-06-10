/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { IconButton } from '@carbon/react';
import clsx from 'clsx';

import type { Agent } from '#modules/agents/api/types.ts';
import { getAgentDisplayName } from '#modules/agents/utils.ts';

import { AgentIcon } from '../components/AgentIcon';
import classes from './AgentHeader.module.scss';
import NewSession from './NewSession.svg';

interface Props {
  agent?: Agent;
  onNewSessionClick?: () => void;
  className?: string;
}

export function AgentHeader({ agent, onNewSessionClick, className }: Props) {
  return (
    <header className={clsx(classes.root, className)}>
      <div>
        {agent && (
          <h1 className={classes.heading}>
            <AgentIcon inverted />

            <span className={classes.name}>{getAgentDisplayName(agent)}</span>
          </h1>
        )}
      </div>

      {onNewSessionClick && (
        <IconButton kind="tertiary" size="sm" label="New session" align="left" autoAlign onClick={onNewSessionClick}>
          <NewSession />
        </IconButton>
      )}
    </header>
  );
}
