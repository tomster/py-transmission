from setuptools import setup, find_packages

# see http://peak.telecommunity.com/DevCenter/setuptools and
# http://docs.python.org/dist/meta-data.html#meta-data for setup signature
dependencies = ["BitTorrent-bencode>=5.0.8"]
setup(
    name = "TransmissionClient",
    version = "0.2rc1",
    packages = find_packages(),

    # metadata for upload to PyPI
    author = "Tom Lazar",
    author_email = "tom@tomster.org",
    description = "Python bindings for the Transmission BitTorrent Client",
    license = "MIT License",
    keywords = "bittorrent transmission",
    url = "http://code.google.com/p/py-transmission/",
    zip_safe = True,
    setup_requires = dependencies,
    install_requires = dependencies,
    test_suite = "test.testTransmissionClient",
    long_description = """Transmission has recently introduced a RPC architecture in which it launches an independent daemon listening on a local socket and exposes a rich API for monitoring and controlling Transmission. This makes it much easier and 'cleaner' to implement clients in other languages, which is what this package aims to do.
""",
    classifiers=["Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Communications :: File Sharing",
    ],
)