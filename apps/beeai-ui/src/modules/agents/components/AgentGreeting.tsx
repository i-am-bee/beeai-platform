/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { memo } from 'react';

import type { Agent } from '../api/types';
import { getAgentDisplayName } from '../utils';
import classes from './AgentGreeting.module.scss';

interface Props {
  agent: Agent;
  className?: string;
  defaultGreeting?: string;
}

export const AgentGreeting = memo(function AgentGreeting({
  agent,
  className,
  defaultGreeting = DEFAULT_GREETING,
}: Props) {
  const userGreetingTemplate = agent.metadata.ui?.user_greeting ?? defaultGreeting;
  const userGreeting = renderVariables(userGreetingTemplate, {
    name: getAgentDisplayName(agent),
  });

  return <h1 className={clsx(classes.root, className)}>{userGreeting}</h1>;
});

function renderVariables(str: string, variables: Record<string, string>): string {
  return str.replace(/{(.*?)}/g, (_, key) => variables[key] ?? `{${key}}`);
}

const DEFAULT_GREETING = `Hi, I am {name}!
How can I help you?`;
