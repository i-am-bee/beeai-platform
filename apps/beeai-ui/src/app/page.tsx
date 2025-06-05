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

import { notFound, redirect } from 'next/navigation';

import { listAgents } from '#modules/agents/api/index.ts';
import { routes } from '#utils/router.ts';

export default async function LandingPage() {
  try {
    const response = await listAgents();
    const firstAgentName = response?.agents.at(0)?.name;

    if (firstAgentName) {
      redirect(routes.agentRun({ name: firstAgentName }));
    }
  } catch (err) {
    // TODO:
    console.log(err);
  }

  return notFound();
}
