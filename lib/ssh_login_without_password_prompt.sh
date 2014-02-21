#!/bin/bash
export HOST=$1
export PORT=$2
export USER=$3
export PASS=$4
# TODO: read timeout from a config file
export TIMEOUT=10

clear
echo "Connecting to $USER@$HOST ..."

script=$( cat <<'END_OF_SCRIPT'
    set timeout $env(TIMEOUT)
	log_user 0
    spawn ssh $env(USER)@$env(HOST) -p $env(PORT)
	log_user 1
    expect {
        "Connection refused" {
            exit 4
        }
        "yes/no" {
            send "yes\r"
            expect {
                "password:" {
                    send "$env(PASS)\r"
                }
                timeout {
                    exit 3
                }
            }
        }
    	"password:" {
    		send "$env(PASS)\r"
    	}
    	timeout {
    		exit 3
    	}
    }
    send "\r"
    interact
END_OF_SCRIPT
)

expect -c "$script"
EXITCODE="$?"

if [ $EXITCODE -eq 3 ]; then
    echo " "
    echo "ERROR: Connection to $HOST:$PORT timed out."
    echo " "
    exit
elif [ $EXITCODE -eq 4 ]; then
    echo " "
    echo "ERROR: Connection to $HOST:$PORT was refused."
    echo "Are IP and port number correct?"
	echo "Or the server could be down?"
    echo " "
    exit
elif [ $EXITCODE -gt "0" ]; then
    echo " "
    echo "ERROR: Error occured while connecting."
    echo "Is the username/password correct?"
    echo " "
	exit
fi
