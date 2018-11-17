import os
import sys
from urlparse import urlparse
import requests

from SimpleFileObject import SimpleFileObject

class HTTPSimpleFileObject(SimpleFileObject):
    """A simple class for working with S3 objects with a file-like interface."""

    def __init__(self, url):
        """
        Construct a HTTPSimpleFileObject.  This object will expose many of the
        methods available to file objects for HTTP(s) urls.

        Args:
            url -- A url of the form "http://address.com/object.name"

        Returns:
            args -- An HTTPSimpleFileObject
        """
        headers = requests.head(url).headers
        if headers.get('Accept-Ranges', None) != 'bytes':
            raise ValueError('URL does not appear to accept byte ranges: {0}'.format(url))

        self._url = url
        self._curr_position = 0
        # If the headers don't specify size for some reason, just assume very large
        self.total_size = int(headers.get('Content-Length', sys.maxint))

        parse_results = urlparse(url)
        self.name = os.path.split(parse_results.path)[-1]


    def read(self, size):
        """
        Read bytes from the HTTP url

        Args:
            size -- The maximum number of bytes to read

        Returns:
            A string of bytes read from the S3 file object
        """
        start_position = self._curr_position
        if size > 0:
            stop_position = start_position+size-1
            self._curr_position += size
        elif size < 0:
            stop_position = ''
            self._curr_position = self.total_size
        else:
            return ''

        headers = {'Range': 'bytes={0}-{1}'.format(start_position, stop_position)}
        result = requests.get(self._url, headers=headers)

        return result.content
