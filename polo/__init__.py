import os
from flask import Flask
from flask_cors import CORS
import polo.config

from logging.config import dictConfig

dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr',  # Default is stderr
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['default'],
            'level': 'WARNING',
            'propagate': False
        },
        '__main__': {  # if __name__ == '__main__'
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False
        },
    }
})

app = Flask(__name__)

if os.environ.get('FLASK_ENV') == 'development':
    app.config.from_object(polo.config.DevelopmentConfig())
elif os.environ.get('FLASK_ENV') == 'test':
    app.config.from_object(polo.config.TestConfig())
elif os.environ.get('FLASK_ENV') == 'demo':
    app.config.from_object(polo.config.DemoConfig())
else:
    app.config.from_object(polo.config.ProductionConfig())

CORS(app)

from polo.database import polo_engine, rm_engines
import polo.api, polo.views, polo.auth
