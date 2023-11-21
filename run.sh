#!/bin/bash

# file: runstop.sh

#----
# Simple script to start / stop / restart a python script in the background.
#----

#----
# To Use:
# Run "./run.sh start" to start, "./run.sh stop" to stop, and "./run.sh restart" to restart.
#----

#----BEGIN EDITABLE VARS----

SCRIPT_TO_EXECUTE_PLUS_ARGS='v2realbot/main.py -u'

OUTPUT_PID_FILE=running.pid

OUTPUT_PID_PATH=$HOME

PYTHON_TO_USE="python3"

# If using 'virtualenv' with python, specify the local virtualenv dir.
#VIRTUAL_ENV_DIR=""

#----END EDITABLE VARS-------

# If virtualenv specified & exists, using that version of python instead.
if [ -d "$VIRTUAL_ENV_DIR" ]; then
    PYTHON_TO_USE="$VIRTUAL_ENV_DIR/bin/python"
fi

start() {
    if [ ! -e "$OUTPUT_PID_PATH/$OUTPUT_PID_FILE" ]; then
        nohup "$PYTHON_TO_USE" ./$SCRIPT_TO_EXECUTE_PLUS_ARGS > strat.log 2>&1 & echo $! > "$OUTPUT_PID_PATH/$OUTPUT_PID_FILE"
        echo "Started $SCRIPT_TO_EXECUTE_PLUS_ARGS @ Process: $!"
        sleep .7
        echo "Created $OUTPUT_PID_FILE file in $OUTPUT_PID_PATH dir"
    else
        echo "$SCRIPT_TO_EXECUTE_PLUS_ARGS is already running."
    fi
}

stop() {
    if [ -e "$OUTPUT_PID_PATH/$OUTPUT_PID_FILE" ]; then
        the_pid=$(<$OUTPUT_PID_PATH/$OUTPUT_PID_FILE)
        rm "$OUTPUT_PID_PATH/$OUTPUT_PID_FILE"
        echo "Deleted $OUTPUT_PID_FILE file in $OUTPUT_PID_PATH dir"
        kill "$the_pid"
        COUNTER=1
        while [ -e /proc/$the_pid ]
        do
            echo "$SCRIPT_TO_EXECUTE_PLUS_ARGS @: $the_pid is still running"
            sleep .7
            COUNTER=$[$COUNTER +1]
            if [ $COUNTER -eq 20 ]; then
                kill -9 "$the_pid"
            fi
            if [ $COUNTER -eq 40 ]; then
                exit 1
            fi
        done
        echo "$SCRIPT_TO_EXECUTE_PLUS_ARGS @: $the_pid has finished"
    else
        echo "$SCRIPT_TO_EXECUTE_PLUS_ARGS is not running."
    fi
}

restart() {
    stop
    sleep 1
    start
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        exit 1
esac

exit 0
