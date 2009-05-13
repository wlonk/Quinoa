#! /bin/sh
### BEGIN INIT INFO
# Provides:          jabber-bot
# Required-Start:    $local_fs $remote_fs
# Required-Stop:     $local_fs $remote_fs
# Default-Start:     2 3 4 5
# Default-Stop:      S 0 1 6
# Short-Description: Starts a jabber bot
# Description:       This file should be used to construct scripts to be
#                    placed in /etc/init.d.
### END INIT INFO

# Author: Kit La Touche <kit.la.t@gmail.com>

# Do NOT "set -e"

PATH=/usr/sbin:/usr/bin:/sbin:/bin
DESC="Jabber bot"
NAME=jabber-bot
DAEMON=/usr/bin/python
PYFILE=bot.py
DAEMON_ARGS="${PYFILE}"
PIDFILE=/var/run/$NAME.pid
SCRIPTNAME=/etc/init.d/$NAME

# Exit if the package is not installed
[ -x "$DAEMON" ] || exit 0
[ -e "$PYFILE" ] || exit 0

#
# Function that starts the daemon/service
#
do_start()
{
    start-stop-daemon --start --background --make-pidfile \
        --pidfile $PIDFILE --chuid jabberbot:jabberbot \
        --exec $DAEMON $DAEMON_ARGS
}

#
# Function that stops the daemon/service
#
do_stop()
{
    start-stop-daemon --stop --pidfile $PIDFILE \
        --exec $DAEMON --retry 4
}

case "$1" in
  start)
    echo "Starting Jabber Bot..."
	do_start
	;;
  stop)
    echo "Stopping Jabber Bot..."
	do_stop
	;;
  restart|force-reload)
    echo "Restarting Jabber Bot..."
	do_stop
    do_start
	;;
  *)
	echo "Usage: $SCRIPTNAME {start|stop|restart|force-reload}" >&2
	exit 3
	;;
esac

:
