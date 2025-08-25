/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from '@carbon/react';
import type { CSSProperties } from 'react';
import { FormProvider, useForm } from 'react-hook-form';

import type { FormRender } from '#api/a2a/extensions/ui/form.ts';

import type { RunFormValues } from '../types';
import { getDefaultValues } from '../utils';
import { FormField } from './FormField';
import classes from './FormRenderer.module.scss';

interface Props {
  definition: FormRender;
  defaultTitle?: string;
  onSubmit: (values: RunFormValues) => void;
}

export function FormRenderer({ definition, defaultTitle, onSubmit }: Props) {
  const { id, title, description, columns, submit_label, fields } = definition;

  const defaultValues = getDefaultValues(fields);

  const form = useForm<RunFormValues>({ defaultValues });

  const heading = title ?? defaultTitle;

  return (
    <FormProvider {...form}>
      <form id={id} className={classes.root} onSubmit={form.handleSubmit(onSubmit)}>
        {heading && <h2 className={classes.heading}>{heading}</h2>}

        {description && <p>{description}</p>}

        <div className={classes.fields} style={{ '--grid-columns': columns } as CSSProperties}>
          {fields.map((field) => (
            <FormField key={field.id} field={field} />
          ))}
        </div>

        <div className={classes.submit}>
          <Button type="submit" size="md">
            {submit_label ?? 'Submit'}
          </Button>
        </div>
      </form>
    </FormProvider>
  );
}
