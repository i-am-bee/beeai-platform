/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { listProviders } from '..';
import { providerKeys } from '../keys';

interface Props {
  id?: string;
  source?: string;
}

export function useProvider({ id, source }: Props) {
  const query = useQuery({
    queryKey: providerKeys.list(),
    // TODO: We could use the `/api/v1/providers/{id}` endpoint to fetch the exact provider, but currently we are listing all the providers at once, so we can reuse the data here untill the providers have sorting and pagination.
    queryFn: listProviders,
    select: (data) => data?.items.find((item) => id === item.id || (source && source === item.source)),
    enabled: Boolean(id),
  });

  return query;
}
