/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { type Agent, InteractionMode } from '#modules/agents/api/types.ts';
import { useHistory } from '#modules/history/contexts/index.ts';

import { ChatView } from '../chat/ChatView';
import { HandsOffView } from '../hands-off/HandsOffView';
import { UiNotAvailableView } from './UiNotAvailableView';

interface Props {
  agent: Agent;
}

export function RunView({ agent }: Props) {
  const { contextId } = useHistory();
  const key = `${agent.name}${contextId ? `:${contextId}` : ''}`;

  switch (agent.ui?.interaction_mode) {
    case InteractionMode.MultiTurn:
      return <ChatView agent={agent} key={key} />;
    case InteractionMode.SingleTurn:
      return <HandsOffView agent={agent} key={key} />;
    default:
      return <UiNotAvailableView agent={agent} />;
  }
}
