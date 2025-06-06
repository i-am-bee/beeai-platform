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

import clsx from 'clsx';

import type { Agent } from '#modules/agents/api/types.ts';
import { getAgentDisplayName } from '#modules/agents/utils.ts';
import { SIDEBAR_VARIANT } from '#utils/vite-constants.ts';

import { AgentIcon } from '../components/AgentIcon';
import classes from './AgentHeader.module.scss';
import { NewSessionButton } from './NewSessionButtton';

interface Props {
  agent?: Agent;
  onNewSessionClick?: () => void;
  className?: string;
  hideButton?: boolean;
}

export function AgentHeader({ agent, onNewSessionClick, className, hideButton }: Props) {
  const sidebarToggleBelowHeader = SIDEBAR_VARIANT === 'toggle-below-header';

  if (sidebarToggleBelowHeader)
    return (
      <div className={clsx(agent && classes.spacing)} id={classes.fixedRoot}>
        {onNewSessionClick && <NewSessionButton onNewSessionClick={onNewSessionClick} fixed />}
      </div>
    );

  if (!agent && hideButton) return null;

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

      {!hideButton && onNewSessionClick && <NewSessionButton onNewSessionClick={onNewSessionClick} />}
    </header>
  );
}
