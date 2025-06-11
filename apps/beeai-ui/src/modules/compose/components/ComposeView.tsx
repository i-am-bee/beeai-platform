/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { SplitPanesView } from '#components/SplitPanesView/SplitPanesView.tsx';

import { useCompose } from '../contexts';
import { SequentialSetup } from '../sequential/SequentialSetup';
import { ComposeResult } from './ComposeResult';

export function ComposeView() {
  const { result } = useCompose();

  return <SplitPanesView leftPane={<SequentialSetup />} rightPane={<ComposeResult />} isSplit={Boolean(result)} />;
}
