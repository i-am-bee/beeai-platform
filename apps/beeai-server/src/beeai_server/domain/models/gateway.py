# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
import re

from typing import Any

from beeai_server.configuration import Configuration
from kink import di
from pydantic import RootModel, HttpUrl, model_validator, ModelWrapValidatorHandler

logger = logging.getLogger(__name__)


class GatewayLocation(RootModel):
    root: HttpUrl

    @model_validator(mode="wrap")
    def _replace_localhost_url(cls, data: Any, handler: ModelWrapValidatorHandler):
        configuration = di[Configuration]
        url: GatewayLocation = handler(data)
        if configuration.provider.self_registration_use_local_network:
            url.root = HttpUrl(re.sub(r"host.docker.internal", "localhost", str(url.root)))
        else:
            # localhost does not make sense in k8s environment, replace it with host.docker.internal for backward compatibility
            url.root = HttpUrl(re.sub(r"localhost|127\.0\.0\.1", "host.docker.internal", str(url.root)))
        return url

    @property
    def is_on_host(self) -> bool:
        """
        Return True for self-registered providers which need to be treated a bit differently
        """
        return any(url in str(self.root) for url in {"host.docker.internal", "localhost", "127.0.0.1"})
