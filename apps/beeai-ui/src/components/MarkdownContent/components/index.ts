/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Components } from 'react-markdown';

import { Code } from './Code';
import { Table } from './Table';

export const components: Components = {
  code: Code,
  table: Table,
};
