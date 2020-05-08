from flask import render_template, request, session
from polo import app
from polo.common import authenticate
import os


@app.route('/')
@authenticate
def get_index():
    folder = request.args.get('folder') or request.args.get('isid')
    plate_ids = request.args.get('plate_ids') or request.args.get('plates') or request.args.get(
        'plate_id') or request.args.get('plate')
    load_source = request.args.get('source_id') or request.args.get('source')
    auth_username = session['username']

    polo_info = os.environ.get('POLO_INFO')
    polo_warning = os.environ.get('POLO_WARNING')
    polo_error = os.environ.get('POLO_ERROR')
    demo_mode = app.config['DEMO']

    env = os.environ

    return render_template('index.html', auth_username=auth_username, folder=folder,
                           plate_ids=plate_ids, load_source=load_source,
                           polo_info=polo_info, polo_warning=polo_warning, polo_error=polo_error,
                           polo_path=request.host + request.path, demo_mode=demo_mode,
                           env=env)


@app.route('/favicon.ico')
def get_favicon():
    return app.send_static_file('images/polo-dark.svg')
