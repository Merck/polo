#!/bin/bash

export FLASK_APP=polo
export FLASK_ENV=test
export OAUTHLIB_INSECURE_TRANSPORT=1 # when using HTTP and not HTTPS

export POLO_INFO="POLO is running in test mode"
#export POLO_WARNING="This is a warning"
#export POLO_ERROR="This is an error message"

flask run -h 0.0.0.0 -p 9002
