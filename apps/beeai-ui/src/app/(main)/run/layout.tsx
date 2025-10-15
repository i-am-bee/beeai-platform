/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { AgentRunLayout } from '#components/layouts/AgentRunLayout.tsx';

export default function RunLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <AgentRunLayout>{children}</AgentRunLayout>;
}
