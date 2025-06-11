/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import remarkGfm from 'remark-gfm';
import type { PluggableList } from 'unified';

export const remarkPlugins = [remarkGfm] satisfies PluggableList;
