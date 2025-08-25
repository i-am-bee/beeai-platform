# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

from types import NoneType
from typing import Literal

from pydantic import BaseModel, Field

from beeai_sdk.a2a.extensions.base import BaseExtensionClient, BaseExtensionServer, BaseExtensionSpec


class BaseField(BaseModel):
    id: str
    label: str
    required: bool | None = None
    col_span: int | None = Field(default=None, ge=1, le=4)


class TextField(BaseField):
    type: Literal["text"]
    placeholder: str | None = None
    default_value: str | None = None

    type: Literal["text"]
    value: str | None = None


class DateField(BaseField):
    type: Literal["date"]
    placeholder: str | None = None
    default_value: str | None = None


class FileItem(BaseModel):
    uri: str
    name: str | None = None
    mime_type: str | None = None


class FileField(BaseField):
    type: Literal["file"]
    accept: list[str]


class OptionItem(BaseModel):
    id: str
    label: str


class MultiSelectField(BaseField):
    type: Literal["multiselect"]
    options: list[OptionItem]
    default_value: list[str] | None = None


class CheckboxField(BaseField):
    type: Literal["checkbox"]
    content: str
    default_value: bool | None = None


FormField = TextField | DateField | FileField | MultiSelectField | CheckboxField


class FormRender(BaseModel):
    id: str
    title: str | None = None
    description: str | None = None
    columns: int | None = Field(default=None, ge=1, le=4)
    submit_label: str | None = None
    fields: list[FormField]


class FormExtensionSpec(BaseExtensionSpec[FormRender]):
    URI: str = "https://a2a-extensions.beeai.dev/ui/form/v1"


class FormExtensionServer(BaseExtensionServer[FormExtensionSpec, NoneType]): ...


class FormExtensionClient(BaseExtensionClient[FormExtensionSpec, FormRender]): ...
