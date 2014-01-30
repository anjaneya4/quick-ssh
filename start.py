#!/usr/bin/env python
# ------------------------------------------------------------------------------
# Author: Ravit Khurana <ravit.khurana@gmail.com>
# ------------------------------------------------------------------------------

import sys
import gtk
import appindicator
import os
import subprocess
import re

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
SERVER_DETAILS_PROPERTIES = BASE_PATH + '/config/server_details.properties'
GET_GUAKE_VISIBILTY_PY = BASE_PATH + '/lib/getGuakeVisibilty.py'
SSH_LOGIN_WITH_PASSWORD_SH = BASE_PATH + '/lib/ssh_login_with_password.sh'
QUICK_SSH_PNG = BASE_PATH + "/res/icons/quick-ssh.png"


class QuickSSHMenu:
    def __init__(self):
        self.ind = appindicator.Indicator(
            "quick-ssh-indicator",
            QUICK_SSH_PNG,
            appindicator.CATEGORY_APPLICATION_STATUS
        )
        self.ind.set_status(appindicator.STATUS_ACTIVE)
        self.menu_setup()
        self.ind.set_menu(self.menu)

    def menu_setup(self):
        self.menu = gtk.Menu()

        self.quit_item = gtk.MenuItem("Quit")
        self.quit_item.connect("activate", self.quit)
        self.quit_item.show()
        self.menu.append(self.quit_item)

        # Reading server details from properties file
        serverDetails = []
        with open(SERVER_DETAILS_PROPERTIES, 'r') as f:
            p = re.compile('^[^=]*')
            for line in f.readlines():
                line = line.strip()
                if line[0] == '#':
                    continue
                else:
                    m = p.match(line)
                    pos_of_equals = m.end()
                    ip = line[0:pos_of_equals].strip()
                    label, username, password = [x.strip() for x in line[pos_of_equals+1:].strip().split(':')]
                    serverDetails.append(
                        {
                            'ip': ip,
                            'label': label,
                            'username': username,
                            'password': password
                        }
                    )

        # Populate the menu
        # TODO: Make the text formating better
        self.item_dict = {}
        for server in serverDetails:
            self.item_dict[server['label']] = gtk.MenuItem(
                "%s@%s\t\t (%s)" % (server['username'], server['ip'], server['label']))
            self.item_dict[server['label']].connect(
                "activate",
                self.generator(server))
            self.item_dict[server['label']].show()
            self.menu.append(self.item_dict[server['label']])

    def main(self):
        gtk.main()

    def quit(self, widget):
        sys.exit(0)

    def generator(self, server):
        return lambda x: self.launchSSH(
            server['ip'] + ' (' + server['label'] + ')',
            server['ip'],
            server['username'],
            server['password'])

    def launchSSH(self, name, ip, username, password):
        if self.isGuakeVisibile():
            os.system('guake -t')
            os.system('guake -t')
        else:
            os.system('guake -t')
        ssh_connect_cmd = "sh %s %s %s %s" % (SSH_LOGIN_WITH_PASSWORD_SH, ip, username, password)
        os.system('guake -n "1" -r "%s" -e "%s"' % (name, ssh_connect_cmd))

    def isGuakeVisibile(self):
        p = subprocess.Popen(
            ['python', GET_GUAKE_VISIBILTY_PY],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out.strip() == 'True':
            return True
        else:
            return False

if __name__ == "__main__":
    indicator = QuickSSHMenu()
    indicator.main()
