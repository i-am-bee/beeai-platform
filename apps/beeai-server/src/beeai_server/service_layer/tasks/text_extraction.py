from procrastinate import Blueprint

blueprint = Blueprint()


@blueprint.task(queue="text_extraction")
async def text_extraction_task(text: str) -> str:
    return text + " hi"
