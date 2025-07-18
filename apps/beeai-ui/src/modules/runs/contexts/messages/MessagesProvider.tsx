/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import { UIMessage } from '#modules/messages/types.ts';

import { MessagesContext } from './messages-context';

interface Props {
  messages: UIMessage[];
}

export function MessagesProvider({ messages, children }: PropsWithChildren<Props>) {
  return <MessagesContext.Provider value={{ messages }}>{children}</MessagesContext.Provider>;
}
