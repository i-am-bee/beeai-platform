/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ArrowRight } from '@carbon/icons-react';
import { Button, ButtonSkeleton } from '@carbon/react';
import clsx from 'clsx';
import isEmpty from 'lodash/isEmpty';
import type { ComponentProps } from 'react';

import { TransitionLink } from '#components/TransitionLink/TransitionLink.tsx';
import { useModal } from '#contexts/Modal/index.tsx';
import { SupportedUis } from '#modules/runs/constants.ts';
import { AddRequiredVariablesModal } from '#modules/variables/components/AddRequiredVariablesModal.tsx';
import { routes } from '#utils/router.ts';

import type { Agent, UiType } from '../api/types';
import { useAgentStatus } from '../hooks/useAgentStatus';
import { useMissingEnvs } from '../hooks/useMissingEnvs';
import classes from './AgentLaunchButton.module.scss';

interface Props {
  agent: Agent;
}

export function AgentLaunchButton({ agent }: Props) {
  const { openModal } = useModal();
  const { provider_id, ui } = agent.metadata;
  const { missingEnvs, isPending: isMissingEnvsPending } = useMissingEnvs({ agent });
  const { isNotInstalled, isInstalling, isInstallError } = useAgentStatus({ providerId: provider_id });

  const uiType = ui?.type;
  const sharedProps: ComponentProps<typeof Button> = {
    kind: 'primary',
    size: 'md',
    className: classes.button,
  };

  if (isNotInstalled || isInstalling || isInstallError) {
    // TODO:
    return null;
  }

  if (uiType && SupportedUis.includes(uiType as UiType)) {
    return (
      // @ts-expect-error as prop mismatch to be resolved later, if component is used again
      <Button
        {...sharedProps}
        renderIcon={ArrowRight}
        disabled={isMissingEnvsPending}
        {...(isEmpty(missingEnvs)
          ? {
              as: TransitionLink,
              href: routes.agentRun({ name: agent.name }),
            }
          : {
              onClick: () => {
                openModal((props) => <AddRequiredVariablesModal {...props} missingEnvs={missingEnvs} />);
              },
            })}
      >
        Launch this agent
      </Button>
    );
  }

  return null;
}

AgentLaunchButton.Skeleton = function AgentLaunchButtonSkeleton() {
  /* .cds--layout--size-md fixes Carbon bug where button size prop is not respected */
  return <ButtonSkeleton size="md" className={clsx('cds--layout--size-md', classes.root)} />;
};
