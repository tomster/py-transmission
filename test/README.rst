The Python Transmission Client
==============================

The Python Transmission Client module is a **Python API** for the `Transmission Bit TorrentClient <http://transmission.m0k.org/index.php>`_. 

Why Python bindings for Transmission?
*************************************

The 'official' BitTorrent software is in fact already implemented in Python: the `Windows, Macintosh Linux GUI clients <http://www.bittorrent.com/download>`_ available at http://www.bittorrent.com/ each contain a standalone python interpreter and lots and lots of python code. Also the command line tools such as ``btlaunch-many`` or ``make-torrent`` are pure python scripts. So why bother with Python bindings for another implementation of the BitTorrent prototcol? Two reasons: **Performance** and **Simplicity**. 

Performance
-----------

`Transmission <http://transmission.m0k.org/index.php>`_ is written in C and *much* more efficient than the official Python client. Running several large torrents with a total throughput of perhaps 1Mb/s can seriously tax even a modern machine and sends your CPU-usage easily up into the 20 - 40% region and will noticably affect the performance of other processes on that machine. With transmission the difference to normal operation becomes hardly even measurable ;-)

Simplicity
----------

Transmission has recently introduced a RPC architecture in which it launches an independant daemon which listens on a local socket for commands and exposes a rich API for monitoring and controlling transmission. This makes it much easier and 'cleaner' to implement clients in other languages, as one doesn't have to deal with issues such as threading or memory management (possibly cross-platform, too!) but rather just needs to implement a simple RPC API. Which is exactly what this package aims to do.

How does it work?
*****************

It does this by providing a wrapper class ``TransmissionClient``, an instance of which represents a locally running ``transmission-daemon`` and provides wrapper methods to (most of) the RPC methods listed in the specification_.

Usage
*****

Simply import the `TransmissionClient` class from the `TransmissionClient` module:

    >>> from TransmissionClient import NoSuchTorrent
    >>> from TransmissionClient import TransmissionClient

To create an instance you must supply the constructor with the path to the socket of a locally running transmission-daemon.

    >>> daemon = TransmissionClient(SOCKETPATH)

**Important note regarding running this test:**

    If you want to *run this doctest* (as opposed to *just reading it for documentation*) you need to first start up an actual instance of ``transmission-daemon`` and then execute this test by calling ``python testTransmissionClient.py <SOCKETPATH>`` where ``SOCKETPATH`` is the path to the socket used by the daemon. On Linux or \*BSD this is typically ``~/.transmission/daemon/socket``, on Mac OSX normally ``$HOME/Library/Application\ Support/Transmission/daemon/socket``, YMMV.

    In order for all tests to pass you need to make sure, that the daemon isn't serving any torrents while running the tests. Also, currently *you will have to restart the daemon before each testrun* -- it will timeout and fail otherwise on subsequent runs because it thinks the torrent added during the second run is a duplicate, eventhough the test cleans up after itself removes it in the final step. This is a `known Transmission bug <http://transmission.m0k.org/trac/ticket/278>`_.

Adding torrents
----------------------------

To add a torrent, simply provide a path to its location using `add_torrent()`. The add method returns a numerical id of the newly added torrent, which is used for all further operations on that torrent  -- more on that later.

Initially, we make sure there aren't any torrents active:

    >>> daemon.remove_all()
    True

    >>> len(daemon.get_status_all())
    0

We add one

    >>> tid = daemon.add_torrent("test/data/test_torrent.torrent")

Now the number of torrents is 1:

    >>> len(daemon.get_status_all())
    1

Trying to add a non-existing torrent file raises a standard ``OSError``:

    >>> daemon.add_torrent("/foo/bar.torrent")
    Traceback (most recent call last):
        ...
    OSError: [Errno 2] No such file or directory: '/foo/bar.torrent'


Status information
------------------

The Transmission API offers *status* and *info* data on torrent(s). You can either request it for a particular torrent by providing its numerical id or request a status or info *list* of all currently known torrents:

    >>> info = daemon.get_info(tid)
    >>> status = daemon.get_status(tid)
    >>> info_all = daemon.get_info_all()
    >>> status_all = daemon.get_status_all()

The actual info or status information is the same, though in each case:

    >>> self.assertEqual(info, info_all[0])
    >>> self.assertEqual(status, status_all[0])

In each case we receive a dictionary. Here are the keys for *status*:

    >>> status.keys()
    ['peers-downloading', 'peers-uploading', 'scrape-leechers', 'swarm-speed', 'error-message', 'state', 'download-speed', 'upload-speed', 'completed', 'scrape-seeders', 'peers-total', 'upload-total', 'running', 'scrape-completed', 'peers-from', 'eta', 'tracker', 'error', 'download-total', 'id']

And here for *info*:

    >>> info.keys()
    ['comment', 'files', 'hash', 'name', 'creator', 'trackers', 'private', 'date', 'path', 'saved', 'id', 'size']

Detailed explanations of the meaning and format of the values returned for the keys mentioned above can be found in the specification_ and are not within the scope of this documentation. Just mentally substitute all occurrences of ``('foo', 'bar')`` with ``['foo', 'bar']`` as it uses (Python) tuples to represent lists.

Calling ``get_info`` and ``get_status`` for non-existing ids raises an exception:

    >>> try:
    ...     info = daemon.get_info(tid+1)
    ...     self.fail()
    ... except NoSuchTorrent, e:
    ...     pass

    >>> try:
    ...     info = daemon.get_status(tid+1)
    ...     self.fail()
    ... except NoSuchTorrent, e:
    ...     pass

Starting and stopping
---------------------

Depending on the global setting, the newly added torrent might be running already. Let's make sure and stop it (the method returns `True` upon success, i.e. the torrent exists and is now stopped):

    >>> daemon.stop(tid)
    True

Now we can start it again (the method returns `True` upon success, i.e. the torrent exists and is now running):

    >>> daemon.start(tid)
    True

Being paranoid, we verify this explicitly:

    >>> daemon.get_status(tid)['running']
    1

Operations on all torrents
--------------------------

The specification_ allows for operations on an arbitrary number of torrents by supplying a list of ids. For the sake of simplicity the Python wrapper supports only operations on single torrents or on *all* torrents at once. In order to test for that, let's first turn autostart off and add some more torrents:

    >>> daemon.set_autostart(False)
    True
    
    >>> tid2 = daemon.add_torrent("test/data/foo_torrent.txt.torrent", autostart=False)

    >>> daemon.get_info(tid2)['name']
    'foo_torrent.txt'

Lo and behold, the new torrent *is not* running:

    >>> daemon.get_status(tid2)['running']
    0

For the third torrent we override the default autostart behaviour by exlicitely passing `autostart=True`

    >>> tid3 = daemon.add_torrent("test/data/bar_torrent.txt.torrent", autostart=True)

    >>> daemon.get_info(tid3)['name']
    'bar_torrent.txt'

However, this doesn't have the expected effect, as the torrent is, in fact, *not* running

    >>> daemon.get_status(tid3)['running']
    0

Now we stop all torrents:

    >>> daemon.stop_all()
    True
    
    >>> daemon.get_status(tid)['running']
    0

    >>> daemon.get_status(tid2)['running']
    0

    >>> daemon.get_status(tid3)['running']
    0

And start them again:

    >>> daemon.start_all()
    True
    
    >>> daemon.get_status(tid)['running']
    1

    >>> daemon.get_status(tid2)['running']
    1

    >>> daemon.get_status(tid3)['running']
    1

Removing torrents
-----------------

To remove a torrent call ``remove_torrent`` with the numerical id of the torrent you want to remove. It will return ``True`` if removal succeeded:

    >>> daemon.remove_torrent(tid)
    True

    >>> len(daemon.get_status_all())
    2

More specifically, it will report ``True`` if the given torrent doesn't exist anymore after calling it, however calling it with the id of a (no longer) existing id raises the aforementioned `NoSuchTorrent` exception:

    >>> try:
    ...     daemon.remove_torrent(tid)
    ...     self.fail()
    ... except NoSuchTorrent, e:
    ...     pass

Finally, we remove all torrents again and leave a clean slate:

    >>> daemon.remove_all()
    True

    >>> len(daemon.get_status_all())
    0

Calling ``remove_all`` even if no torrents are active doesn't raise an exception but instead returns ``True``:

    >>> daemon.remove_all()
    True

Global get- and set methods
---------------------------

Apart from commands dealing with specific torrents, there's a list of basic set- and get methods that all follow the pattern of ``get_foo()`` and ``set_foo(value)`` and that affect the daemon itself:

``get_port`` / ``set_port`` 
    for the port that the daemon listens on (default ``9090``)

``get_directory`` / ``set_directory`` 
    the directory where the downloaded torrents are written to

``get_downlimit`` / ``set_downlimit``
    the maximum (total) download rate in kilobyte, ``-1`` for unlimited

``get_uplimit`` / ``set_uplimit``
    the maximum (total) upload rate in kilobyte, ``-1`` for unlimited

``get_autostart`` / ``set_autostart``
    should newly added torrents be started automatically?

``get_automap`` / ``set_automap``
    enable or disable automatic port mapping on the server.

Let's look at ``get_port`` for example. Since we're running this test against an actual instance of `transmission-daemon`, we'll save the original port value before changing it:

    >>> initial_value = daemon.get_port()

All of the aforementioned set methods provide `True` upon return for success.

    >>> daemon.set_port(9091)
    True

An explicit test confirms this:

    >>> daemon.get_port()
    9091

Finally, we clean up after ourselves and reset (and verify) the original value.

    >>> self.failUnlessEqual(daemon.set_port(initial_value), True)
    >>> daemon.get_port() == initial_value
    True

The remaining methods are tested in a more compact fashion:

    >>> init_downlimit = self.daemon.get_downlimit()
    >>> self.failUnlessEqual(self.daemon.set_downlimit(200), True)
    >>> self.failUnlessEqual(self.daemon.get_downlimit(), 200)
    >>> self.failUnlessEqual(self.daemon.set_downlimit(init_downlimit), True)

    >>> init_uplimit = self.daemon.get_uplimit()
    >>> self.failUnlessEqual(self.daemon.set_uplimit(200), True)
    >>> self.failUnlessEqual(self.daemon.get_uplimit(), 200)
    >>> self.failUnlessEqual(self.daemon.set_uplimit(init_uplimit), True)

    >>> init_autostart = self.daemon.get_autostart()
    >>> self.failUnlessEqual(self.daemon.set_autostart(True), True)
    >>> self.failUnlessEqual(self.daemon.get_autostart(), True)
    >>> self.failUnlessEqual(self.daemon.set_autostart(False), True)
    >>> self.failUnlessEqual(self.daemon.get_autostart(), False)
    >>> self.failUnlessEqual(self.daemon.set_autostart(init_autostart), True)

    >>> init_automap = self.daemon.get_automap()
    >>> self.failUnlessEqual(self.daemon.set_automap(True), True)
    >>> self.failUnlessEqual(self.daemon.get_automap(), True)
    >>> self.failUnlessEqual(self.daemon.set_automap(False), True)
    >>> self.failUnlessEqual(self.daemon.get_automap(), False)
    >>> self.failUnlessEqual(self.daemon.set_automap(init_automap), True)

    >>> init_directory = self.daemon.get_directory()
    >>> self.failUnlessEqual(self.daemon.set_directory("/tmp/foo"), True)
    >>> self.failUnlessEqual(self.daemon.get_directory(), "/tmp/foo")
    >>> self.failUnlessEqual(self.daemon.set_directory(init_directory), True)

For a more detailed explanation refer to the specification_.

Dependencies
************

This packages uses the ``bencode`` and ``bdecode`` implementation of the official BitTorrent client which have been singled out as a `standalone package <http://cheeseshop.python.org/pypi/BitTorrent-bencode/>`_. If you're using an egg-based distribution of this package you won't need to concern yourself with this dependency, though, as it's handled automatically for you.

Credit
******

The Python Transmission Client package was written by Tom Lazar <tom@tomster.org>, http://tomster.org and is licensed under the MIT licence (the same licence as Transmission).

.. _specification: http://transmission.m0k.org/trac/browser/trunk/doc/ipcproto.txt


