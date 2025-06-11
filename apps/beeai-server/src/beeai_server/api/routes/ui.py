# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import fastapi

from beeai_server.configuration import UIFeatureFlags
from beeai_server.api.routes.dependencies import ConfigurationDependency

router = fastapi.APIRouter()


@router.get("/config")
def get_ui_config(config: ConfigurationDependency) -> UIFeatureFlags:
    return config.feature_flags.ui
