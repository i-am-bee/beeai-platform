/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

interface Props extends PropsWithChildren {
  id: string;
}

export function FormLabel({ id, children }: Props) {
  return (
    <label className="cds--label" htmlFor={id}>
      {children}
    </label>
  );
}
