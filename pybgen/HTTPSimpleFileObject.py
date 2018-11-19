import os
import sys
from urlparse import urlparse
from collections import deque
from threading import Lock
import requests

from SimpleFileObject import SimpleFileObject


class HTTPSimpleFileObject(SimpleFileObject):
    """A simple class for working with S3 objects with a file-like interface."""
    _lock = Lock()

    def __init__(self, url):
        """
        Construct a HTTPSimpleFileObject.  This object will expose many of the
        methods available to file objects for HTTP(s) urls.

        Args:
            url -- A url of the form "http://address.com/object.name"

        Returns:
            args -- An HTTPSimpleFileObject
        """
        # Check that the HTTP server supports fetching ranges.
        headers = requests.head(url).headers
        if headers.get('Accept-Ranges', None) != 'bytes':
            raise ValueError('URL does not appear to accept byte ranges: {0}'.format(url))

        self._data_cache = deque()
        self._url = url
        self._curr_remote_position = 0
        self._curr_buffer_position = 0
        # If the headers don't specify size for some reason, just assume very large
        self.total_size = int(headers.get('Content-Length', sys.maxint))

        parse_results = urlparse(url)
        self.name = os.path.split(parse_results.path)[-1]


    def _fill_cache(self, size):
        """
        Read bytes from the HTTP url and place them in our data cache

        Args:
            size -- The maximum number of bytes to read

        Returns:
            None
        """
        # When filling the cache, we are only concerned about the remote
        # position.  The buffer position is handled through set and read.
        start_position = self._curr_remote_position
        if size > 0:
            stop_position = start_position+size-1
            self._curr_remote_position += size
        elif size < 0:
            stop_position = ''
            self._curr_remote_position = self.total_size
        else:
            return ''

        # Now fetch the data from the HTTP server.  Make sure that only one thread
        # or process can use the requests interface at a time.  (Requests does not
        # appear to be thread safe currently).
        HTTPSimpleFileObject._lock.acquire()
        headers = {'Range': 'bytes={0}-{1}'.format(start_position, stop_position)}
        result = requests.get(self._url, headers=headers)
        HTTPSimpleFileObject._lock.release()

        # Insert the data into our cache
        self._data_cache.extend(deque(result.content))
