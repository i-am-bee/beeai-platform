/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import { SplitPanesView } from '#components/SplitPanesView/SplitPanesView.tsx';

import { useHandsOff } from '../contexts/hands-off';
import { HandsOffText } from './HandsOffText';

export function HandsOffView({ children }: PropsWithChildren) {
  const { output } = useHandsOff();

  return <SplitPanesView leftPane={children} rightPane={<HandsOffText />} isSplit={Boolean(output)} spacing="md" />;
}
