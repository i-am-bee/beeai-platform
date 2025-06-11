/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Tab, TabList, TabPanel, TabPanels, Tabs } from '@carbon/react';

import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import { createCodeBlock } from '#utils/markdown.ts';

interface Props {
  cli: string;
}

export function AgentExampleRequests({ cli }: Props) {
  return (
    <Tabs>
      <TabList>
        <Tab>CLI</Tab>
      </TabList>
      <TabPanels>
        <TabPanel tabIndex={-1}>
          <MarkdownContent>{createCodeBlock('bash', cli)}</MarkdownContent>
        </TabPanel>
      </TabPanels>
    </Tabs>
  );
}
