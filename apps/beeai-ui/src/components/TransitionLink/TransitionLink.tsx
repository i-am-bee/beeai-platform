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

import type { LinkProps } from 'next/link';
import Link from 'next/link';
import type { PropsWithChildren } from 'react';

import { useRouteTransition } from '#contexts/TransitionContext/index.ts';

interface Props extends LinkProps {
  className?: string;
}

export function TransitionLink({ href, children, ...props }: PropsWithChildren<Props>) {
  const { transitionTo } = useRouteTransition();

  return (
    <Link
      href={href}
      prefetch={true}
      {...props}
      onClick={(e) => {
        e.preventDefault();
        transitionTo(String(href), { scroll: props.scroll });
      }}
    >
      {children}
    </Link>
  );
}
