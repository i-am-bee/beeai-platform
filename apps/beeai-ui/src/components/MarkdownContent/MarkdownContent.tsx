/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import Markdown from 'react-markdown';

import { components } from './components';
import classes from './MarkdownContent.module.scss';
import { remarkPlugins } from './remark';

interface Props {
  children?: string;
  className?: string;
}

export function MarkdownContent({ className, children }: Props) {
  return (
    <div className={clsx(classes.root, className)}>
      <Markdown remarkPlugins={remarkPlugins} components={components}>
        {children}
      </Markdown>
    </div>
  );
}
