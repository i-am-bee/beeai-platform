/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import * as jose from 'jose';
import type { JWT, JWTDecodeParams } from 'next-auth/jwt';

import type { ProviderConfig } from './types';

// Assisted by watsonx Code Assistant

/**
 * Asynchronously decodes a JWT using a list of providers.
 * This function attempts to verify the JWT against each configured provider's JWKS (JSON Web Key Set) in sequence.
 *
 * @param {JWTDecodeParams} params - The parameters for JWT decoding.
 * @param {ProviderConfig[]} providersConfig - The list of OIDC provider configurations.
 * @returns {Promise<JWT | null>} - A Promise that resolves to the decoded JWT object or null if decoding fails for all providers.
 */
export async function verifyJWTToken(params: JWTDecodeParams, providersConfig: ProviderConfig[]): Promise<JWT | null> {
  let jwt: JWT | null = null;
  let verificationAttempts = 0;

  for (const provider of providersConfig) {
    try {
      const { payload } = await jose.jwtVerify(params?.token || '', provider.JWKS, {
        issuer: provider.issuer,
        audience: provider.client_id,
      });
      payload['id_token'] = params?.token || '';
      jwt = payload;
      break;
    } catch (error) {
      if (error) {
        verificationAttempts += 1;
      }
    }
  }
  if (jwt === null) {
    console.warn(`Unable to verify jwt after trying ${verificationAttempts} providers.`);
  }
  return jwt;
}
