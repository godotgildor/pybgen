import os
import sys
from urlparse import urlparse
from collections import deque
from threading import Lock
import boto3
from SimpleFileObject import SimpleFileObject


class S3SimpleFileObject(SimpleFileObject):
    """A simple class for working with S3 objects with a file-like interface."""

    _lock = Lock()

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
        self._curr_remote_position = 0

        self._data_cache = deque()
        parse_results = urlparse(s3_url)
        self.bucket = parse_results.netloc
        self.key = parse_results.path.lstrip('/')
        self.name = os.path.split(parse_results.path)[-1]

        self._s3_interface = boto3.client('s3')
        self.total_size = int(self._s3_interface.head_object(Bucket=self.bucket,
            Key=self.key)['ContentLength'])


    def _fill_cache(self, size):
        """
        Read bytes from the S3 file object and place them in our data cache

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
            return

        # Now fetch the data from the S3 bucket.  Make sure that only one thread
        # or process can use the S3 interface at a time.  (Boto3 does not
        # appear to be thread safe currently).
        S3SimpleFileObject._lock.acquire()
        data = self._s3_interface.get_object(Bucket=self.bucket,
            Key=self.key,
            Range='bytes={0}-{1}'.format(start_position, stop_position))
        S3SimpleFileObject._lock.release()
        data = data['Body'].read()

        # Insert the data into our cache
        self._data_cache.extend(deque(data))
