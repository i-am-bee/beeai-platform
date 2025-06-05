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

import { useRouter } from '@bprogress/next/app';
import { moderate02 } from '@carbon/motion';
import type { NavigateOptions } from 'next/dist/shared/lib/app-router-context.shared-runtime';
import { usePathname } from 'next/navigation';
import type { PropsWithChildren } from 'react';
import { useCallback, useEffect, useMemo, useRef } from 'react';

import { RouteTransitionContext } from './context';

export function RouteTransitionProvider({ children }: PropsWithChildren) {
  const router = useRouter();
  const pathname = usePathname();

  const transitionControlRef = useRef<{
    element: Element;
    sourcePath: string;
  } | null>(null);

  const pathnameRef = useRef<string>(pathname);
  useEffect(() => {
    pathnameRef.current = pathname;
  }, [pathname]);

  useEffect(() => {
    if (transitionControlRef.current) {
      transitionControlRef.current.element.setAttribute('data-route-transition', 'in');
      transitionControlRef.current = null;
    }
  }, [pathname]);

  const transitionTo = useCallback(
    async (href: string, options?: NavigateOptions) => {
      const element = document.querySelector('[data-route-transition]');
      if (!element || href === pathnameRef.current) {
        router.push(href, options);
        return;
      }

      element.setAttribute('data-route-transition', 'out');
      const sourcePathname = pathnameRef.current;
      setTimeout(() => {
        router.push(href, options);

        if (sourcePathname !== pathnameRef.current) {
          element.setAttribute('data-route-transition', 'in');
        } else {
          transitionControlRef.current = {
            sourcePath: sourcePathname ?? '',
            element,
          };
        }
      }, duration);
    },
    [router],
  );

  const value = useMemo(() => ({ transitionTo }), [transitionTo]);

  return <RouteTransitionContext.Provider value={value}>{children}</RouteTransitionContext.Provider>;
}

const duration = parseFloat(moderate02);
