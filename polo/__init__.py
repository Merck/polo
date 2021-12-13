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

# modify config using suitably-set environment variables
vars = ['OAUTH2_AUTHORIZATION_BASE_URL',
        'OAUTH2_TOKEN_URL',
        'OAUTH2_USERPROFILE_URL',
        'OAUTH2_USERNAME_FIELD',
        'OAUTH2_CLIENT_ID',
        'OAUTH2_CLIENT_SECRET',
        'BYPASS_AUTH',
        'POLO_CONN',
        'RM_BYPASS',
        'DEBUG',
        'DEMO'
        ]

for var in vars:
    if var in os.environ:
        app.config[var] = os.environ.get(var)

# Check if there are any RockMaker configurations set via env vars. Up to 10 are allowed.
app.config['RM_CONN'] = {}
for i in range(10):
    j=str(i)
    if f"RM_{j}_UID" in os.environ and f"RM_{j}_PWD" in os.environ:
        _uid = os.environ.get(f"RM_{j}_UID")
        _pwd = os.environ.get(f"RM_{j}_PWD")
        _database = os.environ.get(f"RM_{j}_DATABASE", "RockMaker")
        app.config['RM_CONN'][i] = f"DSN=ROCKMAKER_{j};UID={_uid};PWD={_pwd};DATABASE={_database}"

CORS(app)

from polo.database import polo_engine, rm_engines
import polo.api, polo.views, polo.auth
