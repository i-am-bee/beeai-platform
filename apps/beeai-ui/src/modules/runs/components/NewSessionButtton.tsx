/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { IconButton } from '@carbon/react';
import clsx from 'clsx';
import { motion } from 'framer-motion';
import type { PropsWithChildren } from 'react';
import { createPortal } from 'react-dom';

import { MainNav } from '#components/layouts/MainNav.tsx';
import { useApp } from '#contexts/App/index.ts';

import NewSession from './NewSession.svg';
import classes from './NewSessionButton.module.scss';

interface Props {
  onNewSessionClick?: () => void;
  fixed?: boolean;
}

export function NewSessionButton({ onNewSessionClick, fixed }: Props) {
  if (!onNewSessionClick) return null;

  const Button = (
    <IconButton
      kind="tertiary"
      size="sm"
      label="New session"
      align={fixed ? 'right' : 'left'}
      autoAlign
      onClick={onNewSessionClick}
      wrapperClasses={classes.button}
    >
      <NewSession />
    </IconButton>
  );

  if (fixed) return <FixedButton>{Button}</FixedButton>;

  return Button;
}

function FixedButton({ children }: PropsWithChildren) {
  const { navigationOpen } = useApp();
  if (!(window && document)) return null;
  return createPortal(
    <div className={clsx(classes.fixed, navigationOpen && classes.navOpen)}>
      <MainNav toggleBelowHeader />
      <motion.div layout="position" transition={{ duration: 0.24 }}>
        {children}
      </motion.div>
    </div>,
    document.body,
  );
}
