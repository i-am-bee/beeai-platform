# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import TYPE_CHECKING
from uuid import UUID

from starlette.status import HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST
from tenacity import retry_if_exception, retry_base

if TYPE_CHECKING:
    from beeai_server.domain.models.provider import ProviderLocation
    from beeai_server.domain.models.agent import EnvVar


class ManifestLoadError(Exception):
    location: "ProviderLocation"
    status_code: int

    def __init__(self, location: "ProviderLocation", message: str | None = None, status_code: int = HTTP_404_NOT_FOUND):
        message = message or f"Manifest at location {location} not found"
        self.status_code = status_code
        super().__init__(message)


class EntityNotFoundError(Exception):
    entity: str
    id: UUID | str

    def __init__(self, entity: str, id: UUID | str):
        self.entity = entity
        self.id = id
        super().__init__(f"{entity} with id {id} not found")


class MissingConfigurationError(Exception):
    def __init__(self, missing_env: list["EnvVar"]):
        self.missing_env = missing_env


class ProviderNotInstalledError(Exception): ...


class DuplicateEntityError(Exception):
    entity: str
    field: str
    value: str | UUID | None
    status_code: int

    def __init__(
        self, entity: str, field: str = "name", value: str | UUID | None = None, status_code: int = HTTP_400_BAD_REQUEST
    ):
        self.entity = entity
        self.field = field
        self.value = value
        self.status_code = status_code
        message = f"Duplicate {entity} found"
        if value:
            message = f"{message}: {field}='{value}' already exists"
        super().__init__(message)


def retry_if_exception_grp_type(*exception_types: type[BaseException]) -> retry_base:
    """Handle also exception groups"""

    def _fn(exception: BaseException) -> bool:
        retry = False
        try:
            raise exception
        except* exception_types:
            retry = True
        except* BaseException:
            ...
        return retry

    return retry_if_exception(_fn)
