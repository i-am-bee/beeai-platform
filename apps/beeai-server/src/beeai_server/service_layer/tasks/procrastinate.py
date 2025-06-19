import re

import procrastinate
from kink import inject

from beeai_server.configuration import Configuration
from beeai_server.service_layer.tasks.text_extraction import blueprint as text_extraction


@inject
def create_app(configuration: Configuration) -> procrastinate.App:
    conn_string = str(configuration.persistence.db_url.get_secret_value())
    conn_string = re.sub("postgresql\+[a-zA-Z]+://", "postgresql://", conn_string)
    app = procrastinate.App(
        connector=procrastinate.PsycopgConnector(
            conninfo=conn_string,
            kwargs={
                "options": f"-c search_path={configuration.persistence.procrastinate_schema}",
            },
        ),
    )
    app.add_tasks_from(blueprint=text_extraction, namespace="text_extraction")
    return app
