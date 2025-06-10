/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { StopFilled } from '@carbon/icons-react';
import { Button } from '@carbon/react';

import { Spinner } from '#components/Spinner/Spinner.tsx';

import { ElapsedTime } from '../components/ElapsedTime';
import { useHandsOff } from '../contexts/hands-off';
import classes from './TaskStatusBar.module.scss';

interface Props {
  onStopClick?: () => void;
}

export function TaskStatusBar({ onStopClick }: Props) {
  const { stats, isPending } = useHandsOff();

  return stats?.startTime ? (
    <div className={classes.root}>
      <div className={classes.label}>
        {isPending && <Spinner center />}
        <span>
          Task {isPending ? 'running for' : 'completed in'} <ElapsedTime stats={stats} />
        </span>
      </div>

      {onStopClick && (
        <Button kind="tertiary" size="sm" renderIcon={StopFilled} onClick={onStopClick}>
          Stop
        </Button>
      )}
    </div>
  ) : null;
}
