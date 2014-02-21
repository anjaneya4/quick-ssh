#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Author: Ravit Khurana <ravit.khurana@gmail.com>
# ----------------------------------------------------------------------------
# TODO: Alert user if title for gnome terminal/guake is set as dynamic

import sys
import gtk
import appindicator
import os
import subprocess
import re

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
SERVER_GROUPS_DIRECTORY = BASE_PATH + '/config/server_groups'
UNGROUPED_SERVERS_CONFIG = BASE_PATH + '/config/ungrouped_servers.config'
SERVER_DETAILS_CONFIG_NAME_PATTERN = "^(.*)\.config$"
GET_GUAKE_VISIBILTY_PY = BASE_PATH + '/lib/getGuakeVisibilty.py'
SSH_LOGIN_WITHOUT_PASSWORD_PROMPT_SH = BASE_PATH + '/lib/ssh_login_without_password_prompt.sh'
SSH_LOGIN_WITH_PASSWORD_PROMPT_SH = BASE_PATH + '/lib/ssh_login_with_password_prompt.sh'
QUICK_SSH_PNG = BASE_PATH + "/res/icons/quick-ssh.png"
DEFAULT_SSH_PORT = 22


class MenuDict(dict):
    """
    This class is a wrapper over gtk.Menu()
    """
    def __init__(self, parent_menuitem, menu=gtk.Menu()):
        super(MenuDict, self)

        if type(menu) == gtk.Menu:
            self.menu = menu
        else:
            raise Exception(
                "Invalid type for menu: %s" % str(type(self.menu))
            )

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
        self.client_type = "ssh"

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

        fileList = [
            filename for filename in os.listdir(SERVER_GROUPS_DIRECTORY)
            if os.path.isfile(os.path.join(SERVER_GROUPS_DIRECTORY, filename))
            and re.match(SERVER_DETAILS_CONFIG_NAME_PATTERN, filename)
        ]

        fileList = sorted(fileList, key=str.lower)

        for server_group_file_name in fileList:
            server_group_name = re.match(
                SERVER_DETAILS_CONFIG_NAME_PATTERN,
                server_group_file_name
            ).group(1)

            self.menu_dict[server_group_name] = MenuDict(
                gtk.MenuItem(server_group_name), gtk.Menu())

            server_menu_dict = self.menu_dict[server_group_name]
            server_menu_dict.show()

            serverDetails = self.fetch_server_group_details(
                "%s/%s" % (
                    SERVER_GROUPS_DIRECTORY, server_group_file_name
                )
            )

            if len(serverDetails) > 0:
                max_user_ip_length = max(
                    len("%s@%s" % (server['username'], server['ip']))
                    for server in serverDetails)

                for server in serverDetails:
                    username_at_ip = "%s@%s" % (server['username'], server['ip'])
                    server_menu_dict[server['label']] = gtk.MenuItem(
                        "%s %s (%s)" % (
                            username_at_ip,
                            " " * (max_user_ip_length - len(username_at_ip)),
                            server['label']
                        )
                    )
                    server_menu_dict[server['label']].connect(
                        "activate",
                        self.generator(server))
                    server_menu_dict[server['label']].show()
            else:
                server_menu_dict["EMPTY"] = gtk.MenuItem(
                    "<EMPTY>"
                )
                server_menu_dict["EMPTY"].set_sensitive(False)
                server_menu_dict["EMPTY"].show()

        # Populate ungrouped servers

        self.menu_dict["seperator2"] = gtk.SeparatorMenuItem()
        self.menu_dict["seperator2"].show()

        serverDetails = self.fetch_server_group_details(
            UNGROUPED_SERVERS_CONFIG
        )
        if len(serverDetails) > 0:
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

        # Populate server groups

        print self.menu_dict.__str__()
        # exit()

    def main(self):
        gtk.main()

    def quit(self, widget):
        sys.exit(0)

    def generator(self, server):
        return lambda x: self.launch_client(server)

    def launch_client(self, server):
        if self.client_type == "ssh":
            self.launch_SSH(
                server['ip'] + ' (' + server['label'] + ')',
                server['ip'],
                server['port'],
                server['username'],
                server['password'])
        elif self.client_type == "sftp":
            self.launch_SFTP(
                server['ip'] + ' (' + server['label'] + ')',
                server['ip'],
                server['port'],
                server['username'],
                server['password'])

    def launch_SSH(self, name, ip, port, username, password):
        if port is None:
            port = DEFAULT_SSH_PORT

        if password is None:
            login_script = SSH_LOGIN_WITH_PASSWORD_PROMPT_SH
        else:
            login_script = SSH_LOGIN_WITHOUT_PASSWORD_PROMPT_SH

        ssh_connect_cmd = "sh %s %s %s %s %s" % (
            login_script,
            ip,
            port,
            username,
            password
        )

        self.Terminals.execute(self.TERMINAL_TO_USE,
                               name=name,
                               cmd=ssh_connect_cmd)

    def launch_SFTP(self, name, ip, port, username, password):
        if port is None:
            port = DEFAULT_SSH_PORT

        os.system("nautilus sftp://%s@%s:%s" % (username, ip, port))

        # if password is None:
        #     login_script = SSH_LOGIN_WITH_PASSWORD_PROMPT_SH
        # else:
        #     login_script = SSH_LOGIN_WITHOUT_PASSWORD_PROMPT_SH

        # ssh_connect_cmd = "sh %s %s %s %s %s" % (
        #     login_script,
        #     ip,
        #     port,
        #     username,
        #     password
        # )

        # self.Terminals.execute(self.TERMINAL_TO_USE,
        #                        name=name,
        #                        cmd=ssh_connect_cmd)

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

    def edit_server_details(self, widget):
        os.system('xdg-open %s' % UNGROUPED_SERVERS_CONFIG)

    def fetch_server_group_details(self, config_file):
        # Reading server details from config file
        serverDetails = []
        with open(config_file, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if line[0] == '#':
                    continue
                else:
                    details_list = [
                        x.strip()
                        for x in line.strip().split(';')]

                    print details_list
                    if len(details_list) == 4:
                        ip_port, label, username, password = details_list
                    elif len(details_list) == 3:
                        ip_port, label, username = details_list
                        password = None
                    else:
                        raise Exception("Invalid entry in file %s" % config_file)

                    ip_port_list = [
                        x.strip()
                        for x in ip_port.strip().split(':')]

                    if len(ip_port_list) == 1:
                        ip = ip_port_list[0]
                        port = None
                    else:
                        ip, port = ip_port_list

                    serverDetails.append(
                        {
                            'ip': ip,
                            'port': port,
                            'label': label,
                            'username': username,
                            'password': password
                        }
                    )

        return serverDetails

if __name__ == "__main__":
    indicator = QuickSSHMenu()
    indicator.main()
