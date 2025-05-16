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

import { Tab, TabList, TabPanel, TabPanels, Tabs } from '@carbon/react';
import { useParams } from 'react-router';

import { SidePanel } from '#components/SidePanel/SidePanel.tsx';
import { useApp } from '#contexts/App/index.ts';

import type { AgentPageParams } from '../types';
import classes from './AgentDetailPanel.module.scss';

export function AgentDetailPanel() {
  const { agentName } = useParams<AgentPageParams>();
  const { agentDetailOpen } = useApp();

  return agentName ? (
    <SidePanel variant="right" isOpen={agentDetailOpen}>
      <div className={classes.tabs}>
        <Tabs>
          <TabList>
            <Tab>Agent details</Tab>

            <Tab disabled>Tools</Tab>
          </TabList>

          <TabPanels>
            <TabPanel>
              <p>TODO: Add agent detail</p>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </div>
    </SidePanel>
  ) : null;
}
