/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { MainContent } from '#components/layouts/MainContent.tsx';
import type { Agent } from '#modules/agents/api/types.ts';
import { SourcesPanel } from '#modules/sources/components/SourcesPanel.tsx';

import { useTasks } from '../../tasks/contexts/tasks-context';
import { RunLandingView } from '../components/RunLandingView';
import { useAgentRun } from '../contexts/agent-run';
import { AgentRunProviders } from '../contexts/agent-run/AgentRunProvider';
import { ChatMessagesView } from './ChatMessagesView';

interface Props {
  agent: Agent;
}

export function ChatView({ agent }: Props) {
  return (
    <AgentRunProviders agent={agent}>
      <Chat />
    </AgentRunProviders>
  );
}

function Chat() {
  const { isPending } = useAgentRun();
  const { tasks } = useTasks();

  const isIdle = !(isPending || tasks.length);

  return (
    <>
      <MainContent spacing="md" scrollable={isIdle}>
        {isIdle ? <RunLandingView /> : <ChatMessagesView />}
      </MainContent>

      <SourcesPanel />
    </>
  );
}
