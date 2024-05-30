import os
from logging import (
    DEBUG,
    ERROR,
    INFO,
    Formatter,
)
from logging.handlers import (
    RotatingFileHandler,
    SMTPHandler,
)

from flask import request
from flask.logging import default_handler

from ..config import basedir


def register_logging(app) -> None:
    class RequestFormatter(Formatter):
        def format(self, record):
            record.url = request.url
            record.remote_addr = request.remote_addr
            return super().format(record)

    request_formatter = RequestFormatter('[%(asctime)s] %(remote_addr)s requested %(url)s\n' '%(levelname)s in %(module)s: %(message)s')

    formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    file_handler = RotatingFileHandler(os.path.join(basedir, 'logs/greybook.log'), maxBytes=10 * 1024 * 1024, backupCount=10)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(INFO)

    mail_handler = SMTPHandler(mailhost=app.config['MAIL_SERVER'], fromaddr=app.config['MAIL_USERNAME'], toaddrs=['ADMIN_EMAIL'], subject='Greybook Application Error', credentials=(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']))
    mail_handler.setLevel(ERROR)
    mail_handler.setFormatter(request_formatter)

    if not app.debug:
        app.logger.addHandler(mail_handler)
        app.logger.addHandler(file_handler)
    else:
        app.logger.setLevel(DEBUG)
        app.logger.addHandler(default_handler)
