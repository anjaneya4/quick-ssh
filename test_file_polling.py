# ------------------------------------------------------------------------------
# This is just a testing file/note
#     - Testing auto-refresh menu on change of server_details.properties
# ------------------------------------------------------------------------------

import os
import threading

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
SERVER_DETAILS_PROPERTIES = BASE_PATH + '/config/server_details.properties'

LAST_MOD_TIME = 0


def get_mod_time():
    return os.stat(SERVER_DETAILS_PROPERTIES).st_mtime


def foo():
    global LAST_MOD_TIME
    if LAST_MOD_TIME != get_mod_time():
        LAST_MOD_TIME = get_mod_time()
        print "Changed"
    threading.Timer(1, foo).start()

foo()
