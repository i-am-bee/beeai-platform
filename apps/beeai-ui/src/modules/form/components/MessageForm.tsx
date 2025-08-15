/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from '@carbon/react';
import type { CSSProperties } from 'react';

import type { UIAgentMessage } from '#modules/messages/types.ts';
import { getMessageForm } from '#modules/messages/utils.ts';

import { FormField } from './FormField';
import classes from './MessageForm.module.scss';

interface Props {
  message: UIAgentMessage;
}

export function MessageForm({ message }: Props) {
  const form = getMessageForm(message);

  if (!form) {
    return null;
  }

  const { id, title, description, columns, submit_label = 'Submit', fields } = form;

  return (
    <form id={id} className={classes.root}>
      {title && <h2>{title}</h2>}

      {description && <p>{description}</p>}

      <div className={classes.fields} style={{ '--grid-columns': columns } as CSSProperties}>
        {fields.map((field) => (
          <FormField key={field.id} field={field} />
        ))}
      </div>

      <Button type="submit">{submit_label}</Button>
    </form>
  );
}
