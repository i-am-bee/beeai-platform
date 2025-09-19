/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { deleteContext } from '..';
import { contextKeys } from '../keys';

interface Props {
  onSuccess?: () => void;
}

export function useDeleteContext({ onSuccess }: Props = {}) {
  const mutation = useMutation({
    mutationFn: deleteContext,
    meta: {
      invalidates: [contextKeys.lists()],
      errorToast: {
        title: 'Failed to delete session.',
        includeErrorMessage: true,
      },
    },
    onSuccess,
  });

  return mutation;
}
