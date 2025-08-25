/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import { getFileContentUrl } from '#modules/files/utils.ts';

import type { A2AServiceExtension, A2AUiExtension } from '../types';

const URI = 'https://a2a-extensions.beeai.dev/ui/form/v1';

const baseField = z.object({
  id: z.string().nonempty(),
  label: z.string().nonempty(),
  required: z.boolean().nullish(),
  col_span: z.number().int().min(1).max(4).nullish(),
});

const textField = baseField.extend({
  type: z.literal('text'),
  placeholder: z.string().nullish(),
  default_value: z.string().nullish(),
});

const textFieldValue = z.object({
  type: textField.shape.type,
  value: z.string().nullish(),
});

const dateField = baseField.extend({
  type: z.literal('date'),
  placeholder: z.string().nullish(),
  default_value: z.string().nullish(),
});

const dateFieldValue = z.object({
  type: dateField.shape.type,
  value: z.string().nullish(),
});

const fileField = baseField.extend({
  type: z.literal('file'),
  accept: z.array(z.string()),
});

const fileFieldValue = z.object({
  type: fileField.shape.type,
  value: z
    .array(
      z.object({
        uri: z.string(),
        name: z.string().nullish(),
        mime_type: z.string().nullish(),
      }),
    )
    .nullish(),
});

const multiSelectField = baseField.extend({
  type: z.literal('multiselect'),
  options: z
    .array(
      z.object({
        id: z.string().nonempty(),
        label: z.string().nonempty(),
      }),
    )
    .nonempty(),
  default_value: z.array(z.string()).nullish(),
});

const multiSelectFieldValue = z.object({
  type: multiSelectField.shape.type,
  value: z.array(z.string()).nullish(),
});

const checkboxField = baseField.extend({
  type: z.literal('checkbox'),
  content: z.string(),
  default_value: z.boolean().nullish(),
});

const checkboxFieldValue = z.object({
  type: checkboxField.shape.type,
  value: z.boolean().nullish(),
});

const fieldSchema = z.discriminatedUnion('type', [textField, dateField, fileField, multiSelectField, checkboxField]);

const renderSchema = z.object({
  id: z.string().nonempty(),
  title: z.string().nullish(),
  description: z.string().nullish(),
  columns: z.number().int().min(1).max(4).nullish(),
  submit_label: z.string().nullish(),
  fields: z.array(fieldSchema).nonempty(),
});

const responseSchema = z.object({
  id: z.string().nonempty(),
  values: z.record(
    z.discriminatedUnion('type', [
      textFieldValue,
      dateFieldValue,
      fileFieldValue,
      multiSelectFieldValue,
      checkboxFieldValue,
    ]),
  ),
});

export type TextField = z.infer<typeof textField>;
export type DateField = z.infer<typeof dateField>;
export type FileField = z.infer<typeof fileField>;
export type MultiSelectField = z.infer<typeof multiSelectField>;
export type CheckboxField = z.infer<typeof checkboxField>;

export type FormField = z.infer<typeof fieldSchema>;

export type FormRender = z.infer<typeof renderSchema>;
export type FormResponse = z.infer<typeof responseSchema>;
export type FormResponseValues = FormResponse['values'][string];

export const formMessageExtension: A2AUiExtension<typeof URI, FormRender> = {
  getMessageMetadataSchema: () => z.object({ [URI]: renderSchema }).partial(),
  getUri: () => URI,
};
export const formExtension: A2AServiceExtension<typeof URI, z.infer<typeof renderSchema>, FormResponse> = {
  getDemandsSchema: () => renderSchema,
  getFulfillmentSchema: () => responseSchema,
  getUri: () => URI,
};

// TODO: Temporary for testing purposes
export const formExtensionRenderExample: FormRender = {
  id: 'form-id',
  title: 'Let’s go on an adventure',
  description: 'Tell me where and whether you are flexible.',
  columns: 2,
  submit_label: 'Continue',
  fields: [
    {
      id: 'location',
      type: 'text',
      label: 'Location',
      placeholder: 'e.g., Japan',
      required: true,
      default_value: 'Japan',
    },
    {
      id: 'departure',
      type: 'date',
      label: 'Departure',
      placeholder: 'mm/dd/yyyy',
      col_span: 1,
      default_value: '12/01/2025',
    },
    {
      id: 'return',
      type: 'date',
      label: 'Return',
      placeholder: 'mm/dd/yyyy',
      col_span: 1,
    },
    {
      id: 'flexible',
      type: 'checkbox',
      label: 'Do you have flexibility with your travel dates?',
      content: 'Yes, I’m flexible',
      default_value: true,
    },
    {
      id: 'notes',
      type: 'file',
      label: 'Upload notes',
      accept: ['text/plain'],
    },
    {
      id: 'interests',
      type: 'multiselect',
      label: 'Interests',
      options: [
        { id: 'cuisine', label: 'Cuisine' },
        { id: 'nature', label: 'Nature' },
        { id: 'nightlife', label: 'Nightlife' },
        { id: 'photography', label: 'Photography' },
        { id: 'volunteering', label: 'Volunteering' },
        { id: 'business', label: 'Business' },
      ],
      default_value: ['cuisine', 'nature'],
    },
  ],
};

// TODO: Temporary for testing purposes
export const formExtensionResponseExample: FormResponse = {
  id: 'form-id',
  values: {
    location: {
      type: 'text',
      value: 'Japan',
    },
    departure: {
      type: 'date',
      value: '10/01/2025',
    },
    return: {
      type: 'date',
      value: '10/15/2025',
    },
    flexible: {
      type: 'checkbox',
      value: true,
    },
    notes: {
      type: 'file',
      value: [
        {
          uri: getFileContentUrl('21be044d-8052-46ef-b1ed-d93fa2cba31e'),
          name: 'test.txt',
          mime_type: 'text/plain',
        },
      ],
    },
    interests: {
      type: 'multiselect',
      value: ['cuisine', 'nightlife', 'photography'],
    },
  },
};
