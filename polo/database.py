"""
database.py
=============
Instantiate SQLAlchemy database engines to be used to connect to:
  * POLO database, as defined in the config.py file
  * One or more RockMaker databases, as defined in the config.py file
"""

import urllib.parse
from sqlalchemy import create_engine
from polo import app

polo_engine = create_engine('mysql://%s' % app.config['POLO_CONN'], pool_pre_ping=True)

rm_engines = {}
for i in app.config['RM_CONN'].keys():
    rm_conn = app.config['RM_CONN'][i]
    params = urllib.parse.quote_plus(rm_conn)
    engine = create_engine("mssql+pyodbc:///?odbc_connect=%s" % params, pool_pre_ping=True)
    rm_engines[i] = engine
