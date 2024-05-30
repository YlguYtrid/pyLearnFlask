import os

from flask import Flask

from .config import CONFIG
from .core.commands import register_commands
from .core.errors import register_errors
from .core.extensions import register_extensions
from .core.logging import register_logging
from .core.request import register_request_handlers
from .core.shell import register_shell_handlers
from .core.templating import register_template_handlers
from .views import register_blueprints


def create_app(config_name: str = os.getenv('FLASK_CONFIG', 'development')) -> Flask:
    if config_name not in CONFIG:
        raise ValueError(f'Invalid config name: {config_name}')
    app = Flask(__name__)
    app.config.from_object(CONFIG[config_name])

    register_blueprints(app)
    register_extensions(app)
    register_logging(app)
    register_commands(app)
    register_errors(app)
    register_template_handlers(app)
    register_request_handlers(app)
    register_shell_handlers(app)

    return app
