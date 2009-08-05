#!/usr/bin/env python

"""
Framework for room-aware jabber bots.
"""

import os
import sys
import xmpp
import time
from regdict import RegDict

class Bot(object):
    """
    This is a base class for a room-aware jabber bot.

    To add commands to the bot, add methods with a signature of (self, msg).
    Then, in the derived class's implementation of register_commands, assign
    that method to a regex-string key in self.commands.
    """
    def __init__(self, jid, resource=None, password=None, log=None):
        self.__last = int(time.strftime('%s', time.localtime()))
        if getattr(log, 'write', False):
            self.__log = log
        else:
            self.__log = sys.stdout
        self.jid = xmpp.JID(jid)
        self.resource = resource or self.__class__.__name__
        self.password = password
        self.rooms = {}
        self.conn = None
        self._finished = False
        self.commands = RegDict() # dict of str -> self.method
        self.commands[r'[Jj]oin\b'] = self.join
        self.commands[r'[Ll]eave\b'] = self.leave
        self.commands[r'[Hh]elp\b'] = self.help
        self.register_commands()
    def log(self, text):
        """
        Send a message to the specified logging service, or stdout
        otherwise.
        """
        self.__log.write("%s: %s" % (self.__class__.__name__, text))
    def register_commands(self):
        """
        Implement this method to associate regex-string commands with
        methods on the bot object.

        This method MUST be implemented.
        """
        raise NotImplementedError
    def on_connect(self):
        """
        Implement this method to define actions to perform right after
        connecting and before entering the serve infinite loop.
        """
        pass
    def periodic_action(self):
        """
        Implement this method to define actions to perform every 10 seconds.
        This can be useful for processing a queue of actions in a delayed
        fashion.
        """
        pass
    def __callback_presence(self, conn, msg):
        presence_type = msg.getType()
        if presence_type == 'subscribe':
            who = msg.getFrom()
            self.conn.send(xmpp.protocol.Presence(to=who, typ='subscribed'))
            self.conn.send(xmpp.protocol.Presence(to=who, typ='subscribe'))
    def __connect(self):
        if not self.conn:
            conn = xmpp.client.Client(self.jid.getDomain(), debug=[])
            if not conn.connect():
                self.log('Unable to connect.')
                return None
            if not conn.auth(self.jid.getNode(), self.password, self.resource):
                self.log('Unable to authorize.')
                return None
            conn.RegisterHandler('message', self.__callback_message)
            conn.RegisterHandler('presence', self.__callback_presence)
            conn.sendInitPresence()
            self.conn = conn
            self.on_connect()
        return self.conn
    def __idle_process(self):
        time.sleep(1)
        now = int(time.strftime('%s', time.localtime()))
        delta = now - self.__last
        if delta > 60:
            self.__last = now
            self.conn.send(xmpp.protocol.Presence())
        if delta % 10 == 0:
            self.periodic_action()
    def serve(self):
        """
        Call this method to connect and begin serving until self._finished
        is True.
        """
        conn = self.__connect()
        if not conn:
            return
        while not self._finished:
            try:
                conn.Process(1)
                self.__idle_process()
            except KeyboardInterrupt:
                break
        return
    def help(self, msg):
        """This provides help, duh."""
        args = msg.getBody()
        try:
            cmd, args = args.split(None, 1)
        except:
            cmd, args = args, ''
        if not args:
            command_list = []
            for kt in self.commands.keys():
                if kt[1].endswith(r'\b'):
                    command_list.append(kt[1][:-2])
                else:
                    if '|' not in kt[1]:
                        command_list.append(kt[1])
            return "Available commands: \n" + \
                "\n".join(" * " + x for x in sorted(command_list)) + \
                "\nRun 'help command' for more information on any command."
        if args in self.commands:
            ret = self.commands[args].__doc__
            return ret
        return "No such command."
    def join(self, msg):
        """Usage: join room@service"""
        args = msg.getBody()
        try:
            cmd, args = args.split(None, 1)
        except:
            cmd, args = args, ''
        try:
            room, serv = args.split('@')
        except:
            return """Usage: join room@service"""
        self.joining = self.__join(room, serv, self.resource)
        name = self.joining.next()
        self.log(name)
        return "Will attempt to join.  See you there."
    def __listen_for_error(self, conn, msg):
        presence_type = msg.getType()
        try:
            if presence_type == 'error' and msg.getErrorCode() == '409':
                self.joining.send(False)
            else:
                self.joining.send(True)
        except StopIteration:
            pass
    def __join(self, roomname, server, resource):
        self.conn.RegisterHandler('presence', self.__listen_for_error)
        while True:
            room_to_join = xmpp.protocol.JID(node=roomname,
                                             domain=server,
                                             resource=resource)
            self.conn.send(xmpp.protocol.Presence(to=room_to_join))
            no_error = (yield)
            if no_error:
                break
            resource += '_'
        self.conn.RegisterHandler('presence', self.__callback_presence)
        self.rooms[roomname + "@" + server] = resource
    def leave(self, msg):
        """Usage: leave room@service"""
        args = msg.getBody()
        try:
            cmd, args = args.split(None, 1)
        except:
            cmd, args = args, ''
        try:
            room, serv = args.split('@')
        except:
            return """Usage: leave room@service"""
        self.__leave(room, serv)
        return "Left."
    def __leave(self, roomname, server):
        room_to_leave = xmpp.protocol.JID(node=roomname,
                    domain=server,
                    resource=self.rooms[roomname + "@" + server])
        self.conn.send(xmpp.protocol.Presence(to=room_to_leave,
                    typ='unavailable',
                    status='So long, and thanks for all the dice?'))
        self.rooms.pop(roomname + "@" + server)
    def _send(self, to_jid, text, type):
        if type == 'groupchat':
            to_jid.setResource('')
        self.conn.send(xmpp.protocol.Message(to_jid, text, type))
    def __callback_message(self, conn, msg):
        for node in msg.getChildren():
            if node.getAttr('xmlns') == "http://jabber.org/protocol/muc#user" \
                    or node.getNamespace() == 'jabber:x:conference':
                roomname = msg.getFrom().getNode()
                servicename = msg.getFrom().getDomain()
                self_msg = xmpp.protocol.Message()
                self_msg.setBody("join %s@%s" % (roomname, servicename))
                return self.join(self_msg)
        text = msg.getBody()
        if msg.getType() == 'groupchat':
            fromroom = msg.getFrom()
            frmstr = fromroom.getNode() + "@" + fromroom.getDomain()
            if frmstr in self.rooms and \
                    self.rooms[frmstr] == fromroom.getResource():
                return
        if not text:
            return
        command = text
        if command in self.commands:
            try:
                reply = self.commands[command](msg)
            except Exception, e:
                reply = "Bad command: %s" % e
            if reply:
                self._send(msg.getFrom(), reply, msg.getType())

if __name__ == "__main__":
    class TestBot(Bot):
        def echo(self, msg):
            text = msg.getBody()
            return text
        def list_rooms(self, msg):
            return ', '.join(self.rooms.keys())
        def whoami(self, msg):
            return "You are %s" % msg.getFrom()
        def register_commands(self):
            self.commands[r'echo\b'] = self.echo
            self.commands[r'rooms$'] = self.list_rooms
            self.commands[r'who am i\??$'] = self.whoami
    b = TestBot('test@transneptune.net', 'Bot', '^^password^^', '')
    b.serve()
