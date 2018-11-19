import os

CACHE_SIZE = 1000000

class SimpleFileObject:
    """A simple cbase lass for working with objects with a file-like interface."""

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
            new_position = self._curr_buffer_position + offset
        else:
            raise ValueError('Invalid value given for parameter whence: {0}'.format(whence))

        if new_position < 0:
            raise ValueError('Invalid final offset: {0}'.format(new_position))

        # Set both the remote and buffer position to this new position and
        # clear the cache.
        self._curr_remote_position = new_position
        self._curr_buffer_position = new_position
        self._data_cache.clear()


    def read(self, size):
        """
        Read bytes from our data cache and return them.  If insufficient
        data is within our data cache, we will fill it.

        Args:
            size -- The maximum number of bytes to read

        Returns:
            A string of bytes read from the S3 file object
        """
        # Make sure our cache has sufficient data to fulfill the request.
        if len(self._data_cache) < size:
            self._fill_cache(max(CACHE_SIZE, size))

        # Extract data from the cache to return to the user.  Increment
        # the buffer position by the number of bytes returned.
        data = ''.join((self._data_cache.popleft() for i in xrange(min(size, len(self._data_cache)))))
        self._curr_buffer_position += len(data)

        return data


    def tell(self):
        """
        Provide the current file position

        Args:
            None

        Returns:
            An integer giving the current file position
        """
        # As far as the user is concerned, the current position is the
        # position we are at in the buffer.  We may have fetched more data though.
        return self._curr_buffer_position


    def close(self):
        """
        Clears the data cache and resets the current postion to the start of the file

        Args:
            None

        Returns:
            None
        """
        # There's no explicit close.  We'll just reset to the beginning of the file object.
        self.seek(0)
