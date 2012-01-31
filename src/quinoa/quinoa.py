#!/usr/bin/env python

"""
Framework for room-aware jabber bots.
"""

import os
import sys
import xmppony as xmpp
import time
from blinker import signal, Signal

class FailedToConnectError(Exception):
    pass

class Conversation(object):
    """
    A basic conversation object.

    This keeps a queue of unprocessed incoming messages, and a queue of
    outgoing responses. It also keeps an id, just in case.

    The messages should be xmppony.protocol.Message objects. Consider using
    xmppony.protocol.Message.buildReply to make an object.
    """
    def __init__(self, id):
        self.id = id
        self.outgoing = signal(id + 'outgoing')

class PresenceConversation(Conversation):
    def __init__(self, *args, **kwargs):
        Conversation.__init__(self, *args, **kwargs)
        signal(self.id).connect(self.check_type)
    def check_type(self, msg):
        if msg.getType() == 'subscribe':
            self.outgoing.send(xmpp.protocol.Presence(to=msg.getFrom(),
                                                        typ='subscribed'))
            self.outgoing.send(xmpp.protocol.Presence(to=msg.getFrom(),
                                                        typ='subscribe'))
        return

class OneToOneConversation(Conversation):
    def __init__(self, *args, **kwargs):
        Conversation.__init__(self, *args, **kwargs)
        signal(self.id).connect(self.reply)
    def reply(self, msg):
        text = msg.getBody()
        if text and text.startswith('echo'):
            reply = []
            for i in range(0, len(text), 5):
                reply.append(text[i:])
            reply = '... '.join(reply)
            self.outgoing.send(msg.buildReply(reply))
        return

class MucConversation(Conversation):
    def __init__(self, *args, **kwargs):
        Conversation.__init__(self, *args, **kwargs)
        signal(self.id).connect(self.reply)
    def reply(self, msg):
        text = msg.getBody()
        if text and text.startswith('echo'):
            reply = []
            for i in range(0, len(text), 5):
                reply.append(text[i:])
            reply = '... '.join(reply)
            out_msg = msg.buildReply(reply)
            out_msg.getTo().setResource('')
            self.outgoing.send(out_msg)
        return

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
        self.conversations = {}
        self.presence_conversations = {}
    def log(self, text):
        """
        Send a message to the specified logging service, or stdout
        otherwise.
        """
        self.__log.write("%s: %s" % (self.__class__.__name__, text))
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
    def __idle_process(self):
        time.sleep(1)
        now = int(time.strftime('%s', time.localtime()))
        delta = now - self.__last
        if delta > 60:
            self.__last = now
            self.conn.send(xmpp.protocol.Presence())
        if delta % 10 == 0:
            self.periodic_action()
    def __callback_message(self, conn, msg):
        for node in msg.getChildren():
            # To handle invites to MUC and groupchat
            if node.getAttr('xmlns') == "http://jabber.org/protocol/muc#user" \
                    or node.getNamespace() == 'jabber:x:conference':
                signal('muc-message-received').send(msg)
                roomname = msg.getFrom().getNode()
                servicename = msg.getFrom().getDomain()
                self_msg = xmpp.protocol.Message()
                self_msg.setBody("join %s@%s" % (roomname, servicename))
                return self.join(self_msg)
        if msg.getType() == 'groupchat':
            frm = str(msg.getFrom())
            if frm not in self.conversations:
                self.conversations[frm] = MucConversation(frm)
                self.conversations[frm].outgoing.connect(self.send)
            signal(frm).send(msg)
        else:
            frm = str(msg.getFrom())
            if frm not in self.conversations:
                self.conversations[frm] = OneToOneConversation(frm)
                self.conversations[frm].outgoing.connect(self.send)
            signal(frm).send(msg)
    def __callback_presence(self, conn, msg):
        frm = str(msg.getFrom())
        if frm not in self.presence_conversations:
            # TODO this is leaking memory, of course. When does it make sense
            # to gc conversations?
            self.presence_conversations[frm] = PresenceConversation(frm)
            self.presence_conversations[frm].outgoing.connect(self.send)
        signal('presence-received').send(msg)
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
    def serve(self):
        """
        Call this method to connect and begin serving until self._finished
        is True.
        """
        conn = self.__connect()
        if not conn:
            raise FailedToConnectError
        while not self._finished:
            try:
                conn.Process(1)
                self.__idle_process()
            except KeyboardInterrupt:
                break
        return
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
    def send(self, msg):
        self.conn.send(msg)
    def _send(self, to_jid, text, type):
        if type == 'groupchat':
            to_jid.setResource('')
        self.conn.send(xmpp.protocol.Message(to_jid, text, type))

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
