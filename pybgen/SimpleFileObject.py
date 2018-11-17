import os

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
