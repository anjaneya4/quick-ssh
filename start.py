#!/usr/bin/env python
# -----------------------------------------------------------------------------
# Author: Ravit Khurana <ravit.khurana@gmail.com>
# -----------------------------------------------------------------------------
# TODO: Alert user if title for gnome terminal/guake is set as dynamic

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
    def __init__(self, parent_menuitem, menu=gtk.Menu()):
        super(MenuDict, self)

        if type(menu) == gtk.Menu:
            self.menu = menu
        else:
            raise Exception("Invalid type for menu: %s" % str(type(self.menu)))

        if parent_menuitem is None:
            self.parent_menuitem = None
        elif type(parent_menuitem) == gtk.MenuItem:
            parent_menuitem.set_submenu(self.menu)
            self.parent_menuitem = parent_menuitem
        else:
            raise Exception("Invalid type for parent_menuitem: %s"
                            % str(type(parent_menuitem)))

    def __setitem__(self, key, val):
        if type(val) not in [MenuDict, gtk.MenuItem, gtk.SeparatorMenuItem]:
            raise Exception("Invalid type %s of val for key \"%s\""
                            % (str(type(val)), str(key)))
        elif type(val) in [gtk.MenuItem, gtk.SeparatorMenuItem]:
            self.menu.append(val)
        elif type(val) in [MenuDict]:
            if val.parent_menuitem is None:
                raise Exception("No parent_menuitem of MenuDict for key: %s."
                                + " Can't add as a submenu" % key)
            self.menu.append(val.parent_menuitem)

        dict.__setitem__(self, key, val)

    def __str__(self, offset=""):
        indent = offset + 4*" "
        key_list = self.keys()
        key_list.extend(["<parent_menuitem>", "<menu>"])
        max_key_length = max(len(key) for key in key_list)

        item_representation = lambda k, v: "%s%s %s=> %s\n" % (
            indent,
            k,
            " " * (max_key_length - len(k)),
            v.__str__(indent + "    " + " "*(max_key_length))
            if type(v) == MenuDict
            else str(v))

        str_dict = "{\n"
        str_dict += item_representation("<parent_menuitem>",
                                        self.parent_menuitem)
        str_dict += item_representation("<menu>", self.menu)
        for k, v in self.iteritems():
            str_dict += item_representation(k, v)
        str_dict += "%s}" % offset
        return str_dict

    def show(self):
        if self.parent_menuitem is not None:
            self.parent_menuitem.show()
        else:
            raise Exception("Not a submenu. parent_menuitem is None")


class QuickSSHMenu:

    class Terminals:
        GUAKE = "Guake Terminal"
        GNOME = "Gnome Terminal"
        XTERM = "Xterm"

        @classmethod
        def isGuakeVisibile(cls):
            p = subprocess.Popen(
                ['python', GET_GUAKE_VISIBILTY_PY],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            out, err = p.communicate()
            if out.strip() == 'True':
                return True
            else:
                return False

        @classmethod
        def execute(cls, terminal, **kwargs):

            if "cmd"in kwargs:
                if terminal == cls.GUAKE:
                    if cls.isGuakeVisibile():
                        os.system('guake -t')
                        os.system('guake -t')
                    else:
                        os.system('guake -t')

                    if "name" in kwargs:
                        os.system('guake -n "1" -r "%s" -e "%s"' % (
                            kwargs["name"],
                            kwargs["cmd"]
                        ))
                    else:
                        os.system('guake -n "1" -e "%s"' % kwargs["cmd"])
                elif terminal == cls.GNOME:
                    if "name" in kwargs:
                        os.system('gnome-terminal --title="%s" -x %s' % (
                            kwargs["name"],
                            kwargs["cmd"]
                        ))
                    else:
                        os.system('gnome-terminal -x %s' % (
                            kwargs["cmd"]
                        ))
                elif terminal == cls.XTERM:
                        os.system('xterm -e %s' % kwargs["cmd"])

            else:
                raise Exception("No command given to execute in %s" % (
                    str(terminal)
                ))

    def __init__(self):
        self.ind = appindicator.Indicator(
            "quick-ssh-indicator",
            QUICK_SSH_PNG,
            appindicator.CATEGORY_APPLICATION_STATUS
        )
        self.ind.set_status(appindicator.STATUS_ACTIVE)
        self.menu_setup()
        self.ind.set_menu(self.menu_dict.menu)

        self.set_terminal(self.Terminals.GUAKE)

    def menu_setup(self):
        self.menu_dict = MenuDict(None)

        # Creating the Quit menu item
        self.menu_dict["quit_item"] = gtk.MenuItem("Quit")
        self.menu_dict["quit_item"].connect("activate", self.quit)
        self.menu_dict["quit_item"].show()

        self.menu_dict["edit_server_details_item"] = gtk.MenuItem(
            "Edit Server Details")
        self.menu_dict["edit_server_details_item"].connect(
            "activate", self.edit_server_details)
        self.menu_dict["edit_server_details_item"].show()

        self.menu_dict["select_terminal"] = MenuDict(
            gtk.MenuItem("Select Terminal"), gtk.Menu())
        self.menu_dict["select_terminal"].show()

        terminals_temp = [
            self.Terminals.GUAKE,
            self.Terminals.GNOME,
            self.Terminals.XTERM
        ]

        for terminal_type in terminals_temp:
            self.menu_dict["select_terminal"][terminal_type] = gtk.MenuItem(
                terminal_type)
            self.menu_dict["select_terminal"][terminal_type].connect(
                "activate",
                self.set_terminal_generator(terminal_type))
            self.menu_dict["select_terminal"][terminal_type].show()

        self.menu_dict["seperator"] = gtk.SeparatorMenuItem()
        self.menu_dict["seperator"].show()

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
                    label, username, password = [
                        x.strip()
                        for x in line[pos_of_equals+1:].strip().split(':')]
                    serverDetails.append(
                        {
                            'ip': ip,
                            'label': label,
                            'username': username,
                            'password': password
                        }
                    )

        # Populate the menu
        max_user_ip_length = max(
            len("%s@%s" % (server['username'], server['ip']))
            for server in serverDetails)

        for server in serverDetails:
            username_at_ip = "%s@%s" % (server['username'], server['ip'])
            self.menu_dict[server['label']] = gtk.MenuItem(
                "%s %s (%s)" % (
                    username_at_ip,
                    " " * (max_user_ip_length - len(username_at_ip)),
                    server['label']
                )
            )
            self.menu_dict[server['label']].connect(
                "activate",
                self.generator(server))
            self.menu_dict[server['label']].show()

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
                self.menu_dict["select_terminal"][term_type].set_label(
                    term_type)

        self.menu_dict["select_terminal"][terminal_type].set_label(
            terminal_type + " *")

    def launchSSH(self, name, ip, username, password):
        ssh_connect_cmd = "sh %s %s %s %s" % (
            SSH_LOGIN_WITH_PASSWORD_SH,
            ip,
            username,
            password
        )

        self.Terminals.execute(self.TERMINAL_TO_USE,
                               name=name,
                               cmd=ssh_connect_cmd)

    def edit_server_details(self, widget):
        os.system('xdg-open %s' % SERVER_DETAILS_PROPERTIES)

if __name__ == "__main__":
    indicator = QuickSSHMenu()
    indicator.main()
