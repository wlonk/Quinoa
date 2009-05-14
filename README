Quinoa
======

This is a simple class for creating Jabber bots capable of joining and
participating in MUC or groupchat.  It depends on xmpppy.

The name was chosen based on the simple fact that I like the grain quinoa, and
I like words starting with Q.

Requirements
============

This package depends on xmpppy.  It also requires a Jabber account if you wish
to actually use a bot.  To set up a useful bot, you will also need to set the
script to run as a daemon somewhere.  All of that is outside the scope of this
package.

Usage
=====

To make a bot, define a subclass of quinoa.Bot.  On this subclass, define
methods to perform the actions you desire.  Any return value of these methods
which does not evaluate to False will be returned as text to the room or person
the bot received the initiating message from.

Further, you must implement a method called register_commands on the subclass,
which will assign the methods defined above to keys in self.commands, a
regex-keyed dictionary.  Bear with me, it's going to get gross for a little
while.  This dictionary subclass takes strings as keys, but interprets them as
regexes.  When an item is retrieved from the dictionary, any string which
matches the regex defined when setting an item will work.  This allows one to
easily define bot commands as regexes, allowing a range of commands to map to
the same method.

Beyond register_commands, there are two optional methods, periodic_action and
on_connect which you can implement.  The first, periodic_action, defines a
method to be called every 10 seconds by the bot, and can be used to handle
items on a to-do queue, for example.  The second, on_connect, defines commands
to be run right after connecting to the server and before entering the
mainloop.  This can be used to set rooms to auto-join at startup, for example.

Examples
========

See quinoa.dicebot for an example of the code in action; it's a bot that rolls
dice for many different roleplaying systems, and responds to some stupid
meme-things.

Contact and Comments
====================

Please email me with suggestions or questions!  My email can be found on the
PyPI page for this project.
