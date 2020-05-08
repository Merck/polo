#!/bin/bash

export FLASK_APP=polo
export FLASK_ENV=production
#export OAUTHLIB_INSECURE_TRANSPORT=1 # when using HTTP and not HTTPS

#export POLO_INFO="This is informational"
#export POLO_WARNING="This is a warning"
#export POLO_ERROR="This is an error message"

flask run -h 0.0.0.0 -p 9002
