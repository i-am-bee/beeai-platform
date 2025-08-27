/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';
import { match } from 'ts-pattern';

import type { FormResponseValues } from '#api/a2a/extensions/ui/form.ts';
import { isNotNull } from '#utils/helpers.ts';

import type { UIMessageForm } from '../types';

interface Props {
  form: UIMessageForm;
}

export function MessageFormResponse({ form }: Props) {
  const data = useMemo(() => {
    return form.request.fields
      .map(({ id, label }) => {
        const value = form.response.values[id];
        return value ? { id, label, value } : null;
      })
      .filter(isNotNull);
  }, [form.request.fields, form.response.values]);

  return (
    <>
      {data.map(({ id, label, value }) => (
        <p key={id}>
          {label}: <FormValueRenderer value={value} />
        </p>
      ))}
    </>
  );
}

function FormValueRenderer({ value }: { value: FormResponseValues }) {
  return match(value)
    .with({ type: 'text' }, { type: 'date' }, ({ value }) => value)
    .otherwise(() => null);
}
