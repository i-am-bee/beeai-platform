/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { IbmGranite } from '@carbon/icons-react';

import { useListVariables } from '#modules/variables/api/queries/useListVariables.ts';
import { AGENT_DISPLAY_MODEL_TEMP } from '#utils/constants.ts';

import { isGraniteModel } from '../utils';
import classes from './AgentModel.module.scss';

export function AgentModel() {
  const { data, isPending } = useListVariables({ errorToast: false, retry: false });

  // TEMP: Fetching the variables list will fail in production deployment,
  // so we check `isPending` and use a fallback once any response is received.
  // This is temporary solution until the agent model is returned by API.
  if (isPending) {
    return null;
  }

  const model = data?.env.LLM_MODEL ?? AGENT_DISPLAY_MODEL_TEMP;

  return (
    <div className={classes.root}>
      {isGraniteModel(model) && <IbmGranite />}
      {model}
    </div>
  );
}
