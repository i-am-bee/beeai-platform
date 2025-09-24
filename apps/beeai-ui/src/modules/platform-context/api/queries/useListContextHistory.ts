/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useInfiniteQuery } from '@tanstack/react-query';

import { isNotNull } from '#utils/helpers.ts';

import { listContextHistory } from '..';
import { contextKeys } from '../keys';
import type { ListContextHistoryParams, ListContextHistoryResponse } from '../types';

type Params = ListContextHistoryParams & {
  initialData?: ListContextHistoryResponse;
};

export function useListContextHistory(params: Params) {
  const { contextId, query: queryParams, initialData } = params;

  const query = useInfiniteQuery({
    queryKey: contextKeys.history(params),
    queryFn: ({ pageParam }: { pageParam?: string }) => {
      return listContextHistory({
        contextId,
        query: {
          ...queryParams,
          page_token: pageParam,
        },
      });
    },
    initialPageParam: undefined,
    getNextPageParam: (lastPage) =>
      lastPage?.has_more && lastPage.next_page_token ? lastPage.next_page_token : undefined,
    select: (data) => {
      if (!data) {
        return undefined;
      }

      const items = data.pages.flatMap((page) => page?.items).filter(isNotNull);

      return items;
    },
    enabled: Boolean(contextId),
    initialData: initialData ? { pages: [initialData], pageParams: [undefined] } : undefined,
  });

  return query;
}
