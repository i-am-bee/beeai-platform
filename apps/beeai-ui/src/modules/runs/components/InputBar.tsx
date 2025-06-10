/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FormEventHandler, PropsWithChildren, ReactNode, Ref, TextareaHTMLAttributes } from 'react';
import { useImperativeHandle, useRef } from 'react';

import { TextAreaAutoHeight } from '#components/TextAreaAutoHeight/TextAreaAutoHeight.tsx';
import { dispatchInputEventOnFormTextarea, submitFormOnEnter } from '#utils/form-utils.ts';

import { AgentModel } from './AgentModel';
import classes from './InputBar.module.scss';

interface Props {
  isSubmitDisabled?: boolean;
  settings?: ReactNode;
  formRef?: Ref<InputBarFormHandle>;
  inputProps?: TextareaHTMLAttributes<HTMLTextAreaElement>;
  onSubmit?: FormEventHandler;
}

export type InputBarFormHandle = {
  resetForm: () => void;
};

export function InputBar({
  isSubmitDisabled,
  settings,
  formRef: formRefProp,
  inputProps,
  onSubmit,
  children,
}: PropsWithChildren<Props>) {
  const formRef = useRef<HTMLFormElement>(null);

  useImperativeHandle(
    formRefProp,
    () => ({
      resetForm() {
        const formElem = formRef.current;
        if (!formElem) return;

        formElem.reset();

        dispatchInputEventOnFormTextarea(formElem);
      },
    }),
    [],
  );

  return (
    <form
      className={classes.root}
      ref={formRef}
      onSubmit={(event) => {
        event.preventDefault();

        if (isSubmitDisabled) return;

        onSubmit?.(event);
      }}
    >
      <TextAreaAutoHeight
        rows={1}
        autoFocus
        {...inputProps}
        className={classes.textarea}
        onKeyDown={(event) => !isSubmitDisabled && submitFormOnEnter(event)}
      />

      <div className={classes.actionBar}>
        <div className={classes.actionBarStart}>
          {settings && <div className={classes.settings}>{settings}</div>}
          <AgentModel />
        </div>

        <div className={classes.submit}>{children}</div>
      </div>
    </form>
  );
}
