from procrastinate import Blueprint


blueprint = Blueprint()


@blueprint.task(queue="text_extraction")
async def extract_text(text: str) -> str:
    return text + " hi"
