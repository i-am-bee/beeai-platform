# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio

from beeai_sdk.platform.client import PlatformClient


async def run(base_url: str = "http://127.0.0.1:18333/api/v1"):
    async with PlatformClient(base_url=base_url) as client:
        response = await client.get("/providers")
        response.raise_for_status()
        print(response.json())


if __name__ == "__main__":
    asyncio.run(run())
