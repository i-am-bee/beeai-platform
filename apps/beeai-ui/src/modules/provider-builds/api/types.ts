/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ApiPath, ApiRequest, ApiResponse } from '#@types/utils.ts';

export type CreateProviderBuildRequest = ApiRequest<'/api/v1/provider_builds'>;
export type CreateProviderBuildResponse = ApiResponse<'/api/v1/provider_builds/{id}'>;

export type ReadProviderBuildPath = ApiPath<'/api/v1/provider_builds/{id}'>;

export type ReadProviderBuildLogsPath = ApiPath<'/api/v1/provider_builds/{id}/logs'>;

export type ProviderBuild = CreateProviderBuildResponse;
