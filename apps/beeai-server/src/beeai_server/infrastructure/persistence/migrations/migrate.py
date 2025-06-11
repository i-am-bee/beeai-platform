# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from datetime import timedelta
from pathlib import Path

from tenacity import retry, wait_fixed, stop_after_delay

from beeai_server import logger

migrations_path = Path(__file__).parent.resolve()


@retry(stop=stop_after_delay(timedelta(minutes=10)), wait=wait_fixed(2), reraise=True)
def _wait_for_db(alembic_cfg):
    from alembic import command

    logger.info("Waiting for database to be ready...")

    command.show(alembic_cfg, "current")


def migrate(wait_for_db: bool = True):
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config(migrations_path / "alembic.ini")
    orig_script_location = alembic_cfg.get_main_option("script_location")
    alembic_cfg.set_main_option("script_location", str(migrations_path / orig_script_location))
    if wait_for_db:
        _wait_for_db(alembic_cfg)

    command.upgrade(alembic_cfg, "head")
