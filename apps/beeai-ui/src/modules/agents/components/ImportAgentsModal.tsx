/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {
  Button,
  InlineLoading,
  ModalBody,
  ModalFooter,
  ModalHeader,
  RadioButton,
  RadioButtonGroup,
  TextInput,
} from '@carbon/react';
import { useCallback, useEffect, useId, useMemo, useState } from 'react';
import { useController, useForm } from 'react-hook-form';

import { CodeSnippet } from '#components/CodeSnippet/CodeSnippet.tsx';
import { Modal } from '#components/Modal/Modal.tsx';
import type { ModalProps } from '#contexts/Modal/modal-context.ts';
import { useCreateProviderBuild } from '#modules/provider-builds/api/mutations/useCreateProviderBuild.ts';
import { useProviderBuildLogs } from '#modules/provider-builds/api/queries/useProviderBuildLogs.ts';
import type { ProviderBuild } from '#modules/provider-builds/api/types.ts';
import { useImportProvider } from '#modules/providers/api/mutations/useImportProvider.ts';
import type { Provider, RegisterProviderRequest } from '#modules/providers/api/types.ts';
import { ProviderSourcePrefixes } from '#modules/providers/constants.ts';
import { ProviderSource } from '#modules/providers/types.ts';
import { maybeParseJson } from '#modules/runs/utils.ts';
import { isNotNull } from '#utils/helpers.ts';

import { useAgent } from '../api/queries/useAgent';
import classes from './ImportAgentsModal.module.scss';

export function ImportAgentsModal({ onRequestClose, ...modalProps }: ModalProps) {
  const id = useId();
  const [registeredProvider, setRegisteredProvider] = useState<Provider>();
  const [providerBuild, setProviderBuild] = useState<ProviderBuild>();
  const { data: agent } = useAgent({ providerId: registeredProvider?.id });

  const { mutateAsync: createProviderBuild } = useCreateProviderBuild();
  const { data: providerBuildLogs } = useProviderBuildLogs({ id: providerBuild?.id });

  const buildLogs = useMemo(
    () =>
      providerBuildLogs
        ?.map(({ data }) => {
          const parsed = maybeParseJson(data);

          if (!parsed) {
            return null;
          }

          const { type, value } = parsed;

          if (type === 'json') {
            const json = JSON.parse(value);
            const message = json.message;

            if (message && typeof message === 'string') {
              return message;
            }
          }

          return value;
        })
        .filter(isNotNull) ?? [],
    [providerBuildLogs],
  );

  const { mutateAsync: importProvider, isPending } = useImportProvider({
    onSuccess: (provider) => {
      if (provider) {
        setRegisteredProvider(provider);
      }
    },
  });

  const {
    register,
    handleSubmit,
    setValue,
    formState: { isValid },
    control,
  } = useForm<FormValues>({
    mode: 'onChange',
    defaultValues: {
      source: ProviderSource.Docker,
    },
  });

  const { field: sourceField } = useController<FormValues, 'source'>({ name: 'source', control });

  const onSubmit = useCallback(
    async ({ location, source }: FormValues) => {
      if (source === ProviderSource.GitHub) {
        const providerBuild = await createProviderBuild({ location });

        setProviderBuild(providerBuild);
      } else if (source === ProviderSource.Docker) {
        await importProvider({ location: `${ProviderSourcePrefixes[source]}${location}` });
      }
    },
    [createProviderBuild, importProvider],
  );

  useEffect(() => {
    setValue('location', '');
  }, [sourceField.value, setValue]);

  return (
    <Modal {...modalProps}>
      <ModalHeader buttonOnClick={() => onRequestClose()}>
        <h2>Import your agent</h2>
      </ModalHeader>

      <ModalBody>
        <form onSubmit={handleSubmit(onSubmit)}>
          <CodeSnippet forceExpand withBorder>
            {buildLogs.join('\n')}
          </CodeSnippet>

          {!registeredProvider && (
            <div className={classes.stack}>
              <RadioButtonGroup
                name={sourceField.name}
                legendText="Select the source of your agent provider"
                valueSelected={sourceField.value}
                onChange={sourceField.onChange}
              >
                <RadioButton labelText="GitHub" value={ProviderSource.GitHub} />
                <RadioButton labelText="Docker image" value={ProviderSource.Docker} />
              </RadioButtonGroup>

              {sourceField.value === ProviderSource.GitHub ? (
                <TextInput
                  id={`${id}:location`}
                  size="lg"
                  className={classes.locationInput}
                  labelText="GitHub repository URL"
                  placeholder="Type your GitHub repository URL"
                  {...register('location', { required: true })}
                />
              ) : (
                <TextInput
                  id={`${id}:location`}
                  size="lg"
                  className={classes.locationInput}
                  labelText="Docker image URL"
                  placeholder="Type your Docker image URL"
                  {...register('location', { required: true })}
                />
              )}
            </div>
          )}

          {registeredProvider && agent && (
            <p className={classes.agents}>
              <strong>{agent.name}</strong> agent installed successfully.
            </p>
          )}
        </form>
      </ModalBody>

      <ModalFooter>
        <Button kind="ghost" onClick={() => onRequestClose()}>
          {isPending || registeredProvider ? 'Close' : 'Cancel'}
        </Button>

        {!registeredProvider && (
          <Button onClick={() => handleSubmit(onSubmit)()} disabled={isPending || !isValid}>
            {isPending ? <InlineLoading description="Importing&hellip;" /> : 'Continue'}
          </Button>
        )}
      </ModalFooter>
    </Modal>
  );
}

type FormValues = RegisterProviderRequest & { source: ProviderSource };
