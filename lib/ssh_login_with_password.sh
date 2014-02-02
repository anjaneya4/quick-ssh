#!/bin/bash
export HOST=$1
export USER=$2
export PASS=$3
# TODO: read timeout from a config file
export TIMEOUT=10

clear
echo "Connecting to $USER@$HOST ..."

script=$( cat <<'END_OF_SCRIPT'
    set timeout $env(TIMEOUT)
	log_user 0
    spawn ssh $env(USER)@$env(HOST)
	log_user 1
    expect {
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
	echo "ERROR: Connection to $HOST timed out."
	exit
elif [ $EXITCODE -gt "0" ]; then
	echo $?
	echo "ERROR: Error occured while connecting. Is the username/password correct?"
	exit
fi
