#!/bin/bash

echo INSTALLING AND CONFIGURING PRECOMPILED FREETDS FOR MSSQL SUPPORT BASED ON ENVIRONMENT VARIABLES
start_dir=`pwd`
freetds=$HOME/.freetds.conf
odbc=$HOME/.odbc.ini

echo Configuring ODBC and FREETDS...

cat > $freetds << EOF-freetds-header
[global]
tds version = 7.1
EOF-freetds-header

# configure up to 10 RockMaker databases
for i in {1..10}; do
    rm_host=RM_${i}_HOST
    if [ ! -z ${!rm_host} ]; then
        echo "   $rm_host set to ${!rm_host}"
        cat >> $freetds << EOF-freetds-host

[ROCKMAKER_${i}]
host = ${!rm_host}
EOF-freetds-host


        rm_port=RM_${i}_PORT
        if [ ! -z ${!rm_port} ]; then
            echo "   $rm_port set to ${!rm_port}"
            cat >> $freetds << EOF-freetds-port
port = ${!rm_port}
EOF-freetds-port
        fi


        rm_instance=RM_${i}_INSTANCE
        if [ ! -z ${!rm_instance} ]; then
            echo "   $rm_instance set to ${!rm_instance}"
            cat >> $freetds << EOF-freetds-instance
instance = ${!rm_instance}
EOF-freetds-instance
        fi

        cat >> $odbc << EOF-odbc
[ROCKMAKER_${i}]
Driver = FreeTDS
Description = RockMaker
Trace = No
Servername = ROCKMAKER_${i}
Database = rockmaker

EOF-odbc

    fi
done

cd $start_dir

