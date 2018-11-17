import os
import sys
from urlparse import urlparse
import requests

class HTTPSimpleFileObject:
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


    def seek(self, offset, whence=0):
        """
        Move to a new file position

        Args:
            offset - The offset byte count
            whence - An optional parameter describing from whence the
                     given offset should be measured.  Valid values are:
                      * 0 (default) - from the start of the file
                      * 1 - relative to the current position
        """
        if whence == 0:
            new_position = offset
        elif whence == 1:
            new_position = self._curr_position + offset
        else:
            raise ValueError('Invalid value given for parameter whence: {0}'.format(whence))

        if new_position < 0:
            raise ValueError('Invalid final offset: {0}'.format(new_position))

        self._curr_position = new_position


    def tell(self):
        """
        Provide the current file position

        Args:
            None

        Returns:
            An integer giving the current file position
        """
        return self._curr_position


    def read(self, size):
        """
        Read bytes from the S3 file object

        Args:
            size -- The maximum number of bytes to read

        Returns:
            A string of bytes read from the S3 file object
        """
        if size > 0:
             stop_position = self._curr_position+size-1
            self._curr_position += size
        elif size < 0:
            stop_position = ''
            self._curr_position = self.total_size
        else:
            return ''

        headers = {'Range': 'bytes={0}-{1}'.format(self._curr_position, stop_position)}
        result = requests.get(self._url, headers=headers)
        data = result.text

        return data
