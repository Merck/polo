#!/bin/bash

echo INSTALLING AND CONFIGURING PRECOMPILED FREETDS FOR MSSQL SUPPORT BASED ON ENVIRONMENT VARIABLES
start_dir=`pwd`

echo Configuring ODBC and FREETDS...
chmod 755 /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so /usr/lib/x86_64-linux-gnu/odbc/libtdsS.so

cat > /etc/odbcinst.ini << EOF-odbcinst
[FreeTDS]
Description = ODBC for FreeTDS
Driver      = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so
Setup       = /usr/lib/x86_64-linux-gnu/odbc/libtdsS.so
FileUsage   = 1
EOF-odbcinst

cd $start_dir
