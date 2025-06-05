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

import { useQuery } from '@tanstack/react-query';

import { PHOENIX_SERVER_TARGET, PROD_MODE } from '#utils/constants.ts';

import { phoenixKeys } from '../keys';

export function usePhoenix() {
  const query = useQuery({
    queryKey: phoenixKeys.all(),
    refetchInterval: PROD_MODE ? 5_000 : false,
    enabled: Boolean(PHOENIX_SERVER_TARGET),
    queryFn: () =>
      fetch(PHOENIX_SERVER_TARGET!, { mode: 'no-cors' })
        .then(() => true)
        .catch(() => false),
  });

  return query;
}
