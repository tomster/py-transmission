from setuptools import setup, find_packages
setup(
    name = "TransmissionClient",
    version = "0.1",
    packages = find_packages(),

    # metadata for upload to PyPI
    author = "Tom Lazar",
    author_email = "tom@tomster.org",
    description = "Python bindings for the Transmission BitTorrentClient",
    license = "MIT License",
    keywords = "bittorrent transmission",
    url = "http://tomster.org/",
    zip_safe = True,
    install_requires = ["BitTorrent-bencode>=5.0.8"],
    test_suite = "test.testTransmissionClient",
    long_description = """The 'official' BitTorrent software is in fact already implemented in Python: the `Windows, Macintosh Linux GUI clients <http://www.bittorrent.com/download>`_ available at http://www.bittorrent.com/ each contain a standalone python interpreter and lots and lots of python code. Also the command line tools such as ``btlaunch-many`` or ``make-torrent`` are pure python scripts. So why bother with Python bindings for another implementation of the BitTorrent prototcol? Two reasons: **Performance** and **Simplicity**. 

Performance
-----------

`Transmission <http://transmission.m0k.org/index.php>`_ is written in C and several orders of magnitude more efficient than the official client. Running several large torrents with a total throughput of perhaps 1Mb/s can seriously tax even a modern machine and sends your CPU-usage easily up into the 20 - 40% region and will noticably affect the performance of other processes on that machine. With transmission the difference becomes hardly even measurable ;-)

Simplicity
----------

Transmission has recently introduced a RPC architecture in which it launches an independant daemon which listens on a local socket for commands and exposes a rich API for monitoring and controlling transmission. This makes it much easier and 'cleaner' to implement clients in other languages, as one doesn't have to deal with issues such as threading or memory management (possibly cross-platform, too!) but rather just needs to implement a simple RPC API. Which is exactly, what this package aims to do.
""",
)