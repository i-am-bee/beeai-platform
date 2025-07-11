# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
import re

from typing import Any

from pydantic import RootModel, HttpUrl, model_validator, ModelWrapValidatorHandler

logger = logging.getLogger(__name__)


class GatewayLocation(RootModel):
    root: HttpUrl

    @model_validator(mode="wrap")
    def _replace_localhost_url(cls, data: Any, handler: ModelWrapValidatorHandler):
        url: GatewayLocation = handler(data)
        url.root = HttpUrl(re.sub(r"localhost|127\.0\.0\.1", "host.docker.internal", str(url.root)))
        return url

    @property
    def is_on_host(self) -> bool:
        """
        Return True for self-registered providers which need to be treated a bit differently
        """
        return any(url in str(self.root) for url in {"host.docker.internal", "localhost", "127.0.0.1"})
