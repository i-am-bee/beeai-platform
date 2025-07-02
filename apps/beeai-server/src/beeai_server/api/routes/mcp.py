# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import fastapi
# from fastapi.responses import StreamingResponse
# import httpx

router = fastapi.APIRouter()


@router.get("/sse")
async def sse(request) -> None:
    return
    # async def sse_stream():
    #     async with httpx.AsyncClient() as client:
    #         async with client.stream("POST", "http") as response:
    #             async for line in response.aiter_lines():
    #                 # Ensure the line is not empty and is valid SSE format
    #                 if line.strip():
    #                     yield line + "\n"  # Forward the SSE event to the client

    # # Return the SSE stream as a StreamingResponse with the correct media type
    # return StreamingResponse(sse_stream(), media_type="text/event-stream")  # noqa: F821
