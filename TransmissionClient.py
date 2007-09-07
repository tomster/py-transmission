#!/usr/bin/env python
# encoding: utf-8

__author__ = "Tom Lazar (tom@tomster.org)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2007/07/29 $"
__copyright__ = "Copyright (c) 2007 Tom Lazar"
__license__ = "MIT License"

"""
TransmissionClient.py

Created by Tom Lazar on 2007-07-29.
Copyright (c) 2007 tomster.org. All rights reserved.
"""
import sys
import getopt
import os
import socket
from bencode import bencode
from bencode import bdecode

class TransmissionClientFailure(Exception): pass
class TransmissionClientNoResponseFailure(TransmissionClientFailure): pass
class InsufficientProtocolVersion(TransmissionClientFailure): pass
class NoSuchTorrent(TransmissionClientFailure): pass

STATUS_TYPES = ["completed", "download-speed", "download-total", "error", "error-message", "eta", "id", "peers-downloading", "peers-from", "peers-total", "peers-uploading", "running", "state", "swarm-speed", "tracker", "scrape-completed", "scrape-leechers", "scrape-seeders", "upload-speed", "upload-total"]

INFO_TYPES = ["id", "hash", "name", "path", "saved", "private", "trackers", "comment", "creator", "date", "size", "files"]

class TransmissionClient(object):
    
    TAGNUMBER = 0
    
    def __init__(self, socketpath="/tmp/transmission-daemon"):
        self.socketpath = socketpath
        self.socket = None

    #
    # internal helper methods:

    def _connect(self, ping=True):
        """ opens a connection to the daemon"""

        if not os.path.exists(self.socketpath):
            raise TransmissionClientFailure, """No socket at %s.
Make sure your daemon is up and running!""" % self.socketpath

        self._close()
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.connect(self.socketpath)
        # 1. we wait for the version info from the server
        answer = self._listen()
        try:
            if answer['version']['max'] < 2:
                raise InsufficientProtocolVersion, \
                    "The server must at least support version 2"
        except KeyError:
            raise TransmissionClientFailure, \
                "received illegal answer from daemon: '%s'" % repr(answer)
        # 2. we send our own version info
        self._send_command_v1({'version' : {'min': 1, 'max': 2}})
        # 3. sending a 'ping' seems to ensure that all following messages receive status messages
        # back from the server:
        if ping:
            self._send_command_v2('noop')
        # now the connection has been established and we can start sending commands

    def _close(self):
        """ if open, closes connection to the daemon"""
        if self.socket is not None:
            self.socket.close()
            self.socket = None

    def _listen(self):
        """Waits for a transmission from the other side and returns it."""
        # First retrieve the eight byte ascii-hex payload length
        try:
            payloadlen = self.socket.recv(8)
        except IOError, (errno, ermess):
            if errno in [32, 57]:
                self._connect()
                payloadlen = self.socket.recv(8)
        try:
            payloadlen = int(payloadlen, 16)
        except ValueError:
            return None
        return bdecode(self.socket.recv(payloadlen))

    def _send_command_v1(self, dictionary):
        """sends a command for protocol version 1. Input is a dictionary with one (or more)
           commands.
        """
        payload = bencode(dictionary)
        hexlength = hex(len(payload))[2:].zfill(8)
        return self.socket.send(hexlength + payload)

    def _send_command_v2(self, command, *parameters):
        """sends a command for protocol version 2. Input is the command name as string
           followed by an arbitrary amount of parameters.
        """

        # we need to add an empty parameter if none is supplied to satisfy the protocol:
        if not parameters:
            parameters = (0,)

        commandlist = [command]
        commandlist.extend(parameters)
        self.TAGNUMBER += 1
        commandlist.append(self.TAGNUMBER)
        payload = bencode(commandlist)
        hexlength = hex(len(payload))[2:].zfill(8)
        encoded = "%s%s" % (hexlength, payload)
        try:
            self.socket.send(encoded)
            return self.TAGNUMBER
        except Exception, info:
            try:
                errno, ermess = info
                if errno in [32, 57]:
                    self._connect(ping=False)
                    self.socket.send(encoded)
                    return self.TAGNUMBER
                elif errno == 61:
                    raise TransmissionClientFailure, """No socket at %s.
Make sure your daemon is up and running!""" % self.socketpath
            except ValueError:
                raise TransmissionClientFailure, "No connection."
        
    def send_receive(self, command, *parameters):
        """expects a command with optional, additional parameters, bencodes it, 
           sends it and returns the answer."""
        if self.socket is None:
            self._connect()
        tag = self._send_command_v2(command, *parameters)
        answer = self._listen()
        while answer[-1] != self.TAGNUMBER:
            answer = self._listen()
        if answer is None:
            raise TransmissionClientNoResponseFailure, "No response from Server. We sent `%s` command with %s as parameters but got nothing back." % (command, repr(parameters))
        else:
            return answer
    
    def send_receive_success(self, command, *parameters):
        """a convenience wrapper to `send_receive` that returns a boolean for the status"""
        return self.send_receive(command, *parameters)[0] == 'succeeded'


    def get_listresponse(self, command, key, *parameters):
        """convenience method for certain get commands that expect the name of the command (with
           additional, optional parameters) and return the answer in a dictionary with a single key,
           i.e. the 'get-port' command returns the port number in a dictionary with the key 'port',
           so we would call `get_listresponse('get-port', 'port')
        """
        try:
            response = self.send_receive(command, *parameters)
        except TransmissionClientNoResponseFailure, e:
            raise TransmissionClientNoResponseFailure, e
        if response[0] == key:
            return response[1]
        else:
            if response[0] in ['failure', 'failed']:
                raise TransmissionClientFailure, \
                    "command `%s` failed." % command
            else:
                raise TransmissionClientFailure, \
                    "invalid response from server: '%s'" % repr(response)

    # public methods from http://transmission.m0k.org/trac/browser/trunk/misc/ipcproto.txt

    def get_downlimit(self):
        """docstring for get_downlimit"""
        return self.get_listresponse('get-downlimit', 'downlimit')

    def set_downlimit(self, limit):
        return self.send_receive_success('downlimit', limit)

    def get_uplimit(self):
        """docstring for get_uplimit"""
        return self.get_listresponse('get-uplimit', 'uplimit')

    def set_uplimit(self, limit):
        return self.send_receive_success('uplimit', limit)

    def get_port(self):
        return self.get_listresponse('get-port', 'port')

    def set_port(self, port):
        return self.send_receive_success('port', port)

    def get_status_all(self):
        return self.get_listresponse('get-status-all', 'status', STATUS_TYPES)

    def get_info_all(self):
        return self.get_listresponse('get-info-all', 'info', INFO_TYPES)

    def get_status(self, id):
        """returns status for one specific torrent"""
        try:
            return self.get_listresponse('get-status', 'status', 
                {'id': [id], 'type': STATUS_TYPES})[0]
        except IndexError:
            raise NoSuchTorrent, "No torrent with id `%d`" % id

    def get_info(self, id):
        """returns info for one specific torrent"""
        try:
            return self.get_listresponse('get-info', 'info', {'id': [id], 'type': INFO_TYPES})[0]
        except IndexError:
            raise NoSuchTorrent, "No torrent with id `%d`" % id

    def stop_all(self):
        """docstring for stop_all"""
        return self.send_receive_success("stop-all")

    def start_all(self):
        """docstring for start_all"""
        return self.send_receive_success("start-all")

    def start(self, id):
        """starts one specific torrent, returns True upon success, False, otherwise"""
        return self.send_receive_success("start", [id,])

    def stop(self, id):
        """stops one specific torrent"""
        return self.send_receive_success("stop", [id,])

    def get_directory(self):
        """returns the path to the directory where the torrents are downloaded to."""
        return self.get_listresponse('get-directory', 'directory')

    def set_directory(self, directory):
        """"""
        return self.send_receive_success('directory', directory)

    def get_autostart(self):
        """returns whether added torrents are started automatically"""
        return bool(self.get_listresponse('get-autostart', 'autostart'))

    def set_autostart(self, autostart):
        """"""
        return self.send_receive_success('autostart', autostart)

    def get_automap(self):
        """returns whether added torrents are mapped automatically"""
        return bool(self.get_listresponse('get-automap', 'automap'))

    def set_automap(self, automap):
        """"""
        return self.send_receive_success('automap', automap)

    def add_torrent(self, file=None, directory=None, autostart=None):
        """ Add the given torrent file. Returns the id of the torrent upon success, None
            otherwise."""
        file = os.path.abspath(file)
        # `getsize` will raise an exception, if the file doesn't exist:
        os.path.getsize(file)
        dictionary = {
            'file': file,
        }
        if directory is not None:
            dictionary['directory'] = directory
        if autostart is not None:
            dictionary['autostart'] = autostart,
        try:
            success = self.get_listresponse("addfile-detailed", "info", dictionary)
            return success[0].get('id', None)
        except TransmissionClientNoResponseFailure:
            return None

    def remove_torrent(self, id):
        """Remove the torrent with the given id. Returns `True` upon success, `False` otherwise."""
        # first we check, if that torrent exists. if not, `get_info` will raise an exception
        self.get_info(id)
        return self.send_receive_success("remove", [id,])

    def remove_all(self):
        """Removes ''all'' torrents. Returns `True` upon success."""
        return self.send_receive_success("remove-all")

    def ping(self):
        return self.send_receive_success("noop")
        
def usage():
    print """usage:
    
        TransmissionClient [options] socketpath
        
        You must provide a full path to the socket of a locally running transmission-daemon.
        
        Options:
        
        -d --debug                  Enter a pdb prompt with the running daemon bound to local
                                    variable `daemon`.
        -a --add-torrent <file>     Add (and autostart) the torrent
        """

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "da:", ["debug", "add-torrent="])
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)
    if opts:
        daemon = TransmissionClient(args[0])
        for opt, arg in opts:
            if opt in ("-d", "--debug"):
                print """---------------------------------------------------------------------------
Entering interactive debug session. Daemon bound to local variable `daemon`.
---------------------------------------------------------------------------
"""
                import pdb ; pdb.set_trace( )
            elif opt in ("-a", "--add-torrent"):
                success = daemon.add_torrent(arg)
                if success:
                    print "added torrent (id=%d)" % success
                else:
                    print "failed to add torrent (daemon gave no reason)"
    else:
        usage()

if __name__ == "__main__":
    main()
