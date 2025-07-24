/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Container } from '#components/layouts/Container.tsx';
import { AgentGreeting } from '#modules/agents/components/AgentGreeting.tsx';

import { FileUpload } from '../../files/components/FileUpload';
import { useAgentRun } from '../contexts/agent-run';
import { RunInput } from './RunInput';
import classes from './RunLandingView.module.scss';

export function RunLandingView() {
  const { agent } = useAgentRun();
  const {
    ui: { prompt_suggestions },
  } = agent;

  return (
    <FileUpload>
      <Container size="sm" className={classes.root}>
        <AgentGreeting agent={agent} />

        <RunInput promptSuggestions={prompt_suggestions} />
      </Container>
    </FileUpload>
  );
}
