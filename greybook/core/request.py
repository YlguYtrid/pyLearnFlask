from flask_sqlalchemy.record_queries import get_recorded_queries
from werkzeug.wrappers.response import Response


def register_request_handlers(app) -> None:
    @app.after_request
    def query_profiler(response: Response) -> Response:
        for q in get_recorded_queries():
            if q.duration >= app.config['GREYBOOK_SLOW_QUERY_THRESHOLD']:
                app.logger.warning('Slow query: Duration: ' f'{q.duration:f}s\n Context: {q.context}\nQuery: {q.statement}\n')  # type: ignore # noqa: G004
        return response
