/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FormField, FormResponseValues } from '#api/a2a/extensions/ui/form.ts';

export type RunFormValues = Record<string, FormResponseValues>;

export type ValuesOfField<F extends FormField> = Record<string, Extract<FormResponseValues, { type: F['type'] }>>;
