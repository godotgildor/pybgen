import os
from urlparse import urlparse
import boto3

class S3SimpleFileObject:
    """A simple class for working with S3 objects with a file-like interface."""

    def __init__(self, s3_url):
        """
        Construct a S3SimpleFileObject.  This object will expose many of the
        methods available to file objects for objects that live in S3.

        Note: This class assumes that the AWS access key values are either
        stored as environmental variables or are present in an AWS credentials 
        file.

        Args:
            s3_url -- A url of the form "s3://bucket/object.name"

        Returns:
            args -- An S3SimpleFileObject
        """
        self._s3_url = s3_url
        self._curr_position = 0

        parse_results = urlparse(s3_url)
        self.bucket = parse_results.netloc
        self.name = os.path.split(parse_results.path)[-1]

        self._s3_interface = boto3.client('s3')


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
        elif size < 0:
            stop_position = ''
        else:
            return ''


        data = self._s3_interface.get_object(Bucket=self.bucket,
            Key=self.name,
            Range='bytes={0}-{1}'.format(self._curr_position, stop_position))
        data = data['Body'].read()
        self._curr_position += size

        return data
