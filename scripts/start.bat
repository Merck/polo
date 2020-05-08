set FLASK_APP=polo
set FLASK_ENV=development
set OAUTHLIB_INSECURE_TRANSPORT=1

REM set POLO_INFO=This is informational
REM set POLO_WARNING=This is a warning
REM set POLO_ERROR=This is an error message

flask run -h 0.0.0.0 -p 9002
