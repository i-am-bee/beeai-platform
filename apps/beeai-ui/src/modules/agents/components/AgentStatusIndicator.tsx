/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { InlineLoading } from '@carbon/react';

import type { Agent } from '../api/types';
import { useAgentStatus } from '../hooks/useAgentStatus';
import classes from './AgentStatusIndicator.module.scss';

interface Props {
  agent: Agent;
}

export function AgentStatusIndicator({ agent }: Props) {
  const { provider_id } = agent.metadata;
  const { isInstalling } = useAgentStatus({ providerId: provider_id });

  if (isInstalling) {
    return (
      <div className={classes.root}>
        <InlineLoading />
      </div>
    );
  }
  return null;
}
