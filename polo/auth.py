"""
auth.py
========================
Routes required for OAuth2-based authentication
"""
from requests_oauthlib import OAuth2Session
from flask import request, redirect, session
import os
import sys
from polo import app

app.secret_key = os.urandom(24)


@app.route("/auth")
def auth():
    auth = OAuth2Session(app.config['OAUTH2_CLIENT_ID'])
    method = request.args.get('method')
    if method is None or method not in ('sso', 'form'):
        method = 'sso'

    app.logger.info("Authentication attempt using method {}".format(method))
    authorization_url, state = auth.authorization_url(app.config['OAUTH2_AUTHORIZATION_BASE_URL'], login_method=method)
    session['oauth_state'] = state
    return redirect(authorization_url)


@app.route("/callback", methods=["GET"])
def callback():
    try:
        auth = OAuth2Session(app.config['OAUTH2_CLIENT_ID'], state=session['oauth_state'])
        token = auth.fetch_token(app.config['OAUTH2_TOKEN_URL'],
                                 client_secret=app.config['OAUTH2_CLIENT_SECRET'],
                                 authorization_response=request.url)

        session['oauth_token'] = token
        session['username'] = auth.get(app.config['OAUTH2_USERPROFILE_URL']).json()[app.config['OAUTH2_USERNAME_FIELD']]
        app.logger.info("Authentication successful as user {}".format(session['username']))
        return redirect('/')
    except:  # catch all exceptions
        error = sys.exc_info()[0]
        print("==> ERROR", error)
        return redirect('/auth')
