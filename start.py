#!/usr/bin/env python
# ------------------------------------------------------------------------------
# Author: Ravit Khurana <ravit.khurana@gmail.com>
# ------------------------------------------------------------------------------
# TODO: Alert user if title for gnome terminal/guake is set as dynamic
# TODO: Let user choose which terminal he/she wants to use
# TODO: Create a dict/list which would hold reference to all the menuitems and menus

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


class MenuDict(dict):
    # TODO:
    #   Impletement this class such that the order of element is preserved
    def __init__(self, parent_menuitem, menu=gtk.Menu()):
        super(MenuDict, self)

        self.parent_menuitem = parent_menuitem
        self.menu = menu

        if type(self.menu) == gtk.Menu:
            pass
        else:
            raise Exception("Invalid type for menu: %s" % str(type(self.menu)))

        if self.parent_menuitem is None:
            pass
        elif type(self.parent_menuitem) == gtk.MenuItem:
            self.parent_menuitem.set_submenu(self.menu)
        else:
            raise Exception("Invalid type for parent_menuitem: %s" % str(type(self.parent_menuitem)))

    def __setitem__(self, key, val):
        if type(val) not in [MenuDict, gtk.MenuItem, gtk.SeparatorMenuItem]:
            raise Exception("Invalid type %s of val for key \"%s\"" % (str(type(val)), str(key)))
        else:
            print "Added %s => %s" % (key, val)
            dict.__setitem__(self, key, val)

    def __str__(self, offset=""):
        indent = offset + 4*" "
        key_list = self.keys()
        key_list.extend(["<parent_menuitem>", "<menu>"])
        max_key_length = max(len(key) for key in key_list)
        item_representation = lambda k, v: "%s%s %s=> %s\n" % (indent, k, " " * (max_key_length - len(k)), v.__str__(indent + "    " + " "*(max_key_length)) if type(v) == MenuDict else str(v))
        str_dict = "{\n"
        str_dict += item_representation("<parent_menuitem>", self.parent_menuitem)
        str_dict += item_representation("<menu>", self.menu)
        for k, v in self.iteritems():
            str_dict += item_representation(k, v)
        str_dict += "%s}" % offset
        return str_dict


class QuickSSHMenu:

    class TERMINALS:
        GUAKE = "Guake Terminal"
        GNOME = "Gnome Terminal"
        XTERM = "Xterm"

    def __init__(self):
        self.ind = appindicator.Indicator(
            "quick-ssh-indicator",
            QUICK_SSH_PNG,
            appindicator.CATEGORY_APPLICATION_STATUS
        )
        self.ind.set_status(appindicator.STATUS_ACTIVE)
        self.menu_setup()
        self.ind.set_menu(self.menu_dict.menu)

        self.set_terminal(self.TERMINALS.GUAKE)

    def menu_setup(self):
        self.menu_dict = MenuDict(None)

        # Creating the Quit menu item
        self.menu_dict["quit_item"] = gtk.MenuItem("Quit")
        self.menu_dict["quit_item"].connect("activate", self.quit)
        self.menu_dict["quit_item"].show()
        # TODO: The MenuItem should get automatically appended to the menu
        #       Make changes in the class MenuDict(dict)
        self.menu_dict.menu.append(self.menu_dict["quit_item"])

        self.menu_dict["edit_server_details_item"] = gtk.MenuItem("<< Edit Server Details >>")
        self.menu_dict["edit_server_details_item"].connect("activate", self.edit_server_details)
        self.menu_dict["edit_server_details_item"].show()
        self.menu_dict.menu.append(self.menu_dict["edit_server_details_item"])

        self.menu_dict["select_terminal"] = MenuDict(gtk.MenuItem("Select Terminal"), gtk.Menu())
        self.menu_dict["select_terminal"].parent_menuitem.show()
        self.menu_dict.menu.append(self.menu_dict["select_terminal"].parent_menuitem)

        terminals_temp = [
            self.TERMINALS.GUAKE,
            self.TERMINALS.GNOME,
            self.TERMINALS.XTERM
        ]

        for terminal_type in terminals_temp:
            self.menu_dict["select_terminal"][terminal_type] = gtk.MenuItem(terminal_type)
            self.menu_dict["select_terminal"][terminal_type].connect(
                "activate",
                self.set_terminal_generator(terminal_type))
            self.menu_dict["select_terminal"][terminal_type].show()
            self.menu_dict["select_terminal"].menu.append(self.menu_dict["select_terminal"][terminal_type])

        self.menu_dict["seperator"] = gtk.SeparatorMenuItem()
        self.menu_dict["seperator"].show()
        self.menu_dict.menu.append(self.menu_dict["seperator"])

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
        max_user_ip_length = max(len("%s@%s" % (server['username'], server['ip'])) for server in serverDetails)

        for server in serverDetails:
            username_at_ip = "%s@%s" % (server['username'], server['ip'])
            self.menu_dict[server['label']] = gtk.MenuItem(
                "%s %s (%s)" % (username_at_ip, " " * (max_user_ip_length - len(username_at_ip)), server['label']))
            self.menu_dict[server['label']].connect(
                "activate",
                self.generator(server))
            self.menu_dict[server['label']].show()
            self.menu_dict.menu.append(self.menu_dict[server['label']])

        print self.menu_dict.__str__()
        # exit()

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

    def set_terminal_generator(self, terminal_type):
        return lambda x: self.set_terminal(terminal_type)

    def set_terminal(self, terminal_type):
        self.TERMINAL_TO_USE = terminal_type
        for term_type in self.menu_dict["select_terminal"]:
            if term_type != "_submenu" and term_type != "_menuitem":
                self.menu_dict["select_terminal"][term_type].set_label(term_type)

        # TODO: Display active terminal in a more elegant manner
        self.menu_dict["select_terminal"][terminal_type].set_label(terminal_type + " *")

    def launchSSH(self, name, ip, username, password):
        ssh_connect_cmd = "sh %s %s %s %s" % (SSH_LOGIN_WITH_PASSWORD_SH, ip, username, password)

        # TODO: Change implementation to be able to choose between more
        #       than two terminals
        if self.TERMINAL_TO_USE == self.TERMINALS.GUAKE:
            if self.isGuakeVisibile():
                os.system('guake -t')
                os.system('guake -t')
            else:
                os.system('guake -t')
            os.system('guake -n "1" -r "%s" -e "%s"' % (name, ssh_connect_cmd))
        else:
            os.system('gnome-terminal --title="%s" -x %s' % (name, ssh_connect_cmd))

    def edit_server_details(self, widget):
        os.system('xdg-open %s' % SERVER_DETAILS_PROPERTIES)

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
