/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Checkbox, TextInput } from '@carbon/react';
import type { CSSProperties } from 'react';
import { match } from 'ts-pattern';

import { FormLabel } from '#components/FormLabel/FormLabel.tsx';

import type { FormField } from '../types';
import classes from './FormField.module.scss';

interface Props {
  field: FormField;
}

export function FormField({ field }: Props) {
  const { col_span } = field;

  return (
    <div className={classes.root} style={{ '--col-span': col_span } as CSSProperties}>
      <FieldRenderer field={field} />
    </div>
  );
}

function FieldRenderer({ field }: Props) {
  const { id, label, required } = field;

  return match(field)
    .with({ type: 'text' }, ({ placeholder, default_value }) => (
      <TextInput id={id} labelText={label} placeholder={placeholder} required={required} defaultValue={default_value} />
    ))
    .with({ type: 'checkbox' }, ({ content, default_checked }) => (
      <>
        <FormLabel id={id}>{label}</FormLabel>

        <Checkbox id={id} labelText={content} required={required} defaultChecked={default_checked} />
      </>
    ))
    .exhaustive();
}
