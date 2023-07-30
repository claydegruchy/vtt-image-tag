
from __future__ import with_statement
import argparse

from functools import wraps
import os
import sys
import errno
import logging

from fuse import FUSE, FuseOSError, Operations
import inspect


log = logging.getLogger(__name__)


def logged(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        log.info('%s(%s)', f.__name__, ','.join(
            [str(item) for item in args[1:]]))
        return f(*args, **kwargs)
    return wrapped


# Path to the file you want to return regardless of the requested filename
target_file_path = "/home/user/lmao.txt"

# regex for getting everything between """
# regex = re.compile(r'"""(.*?)"""', re.DOTALL)


class Passthrough(Operations):
    """A simple passthrough interface.

    Initialize the filesystem. This function can often be left unimplemented, but
    it can be a handy way to perform one-time setup such as allocating
    variable-sized data structures or initializing a new filesystem. The
    fuse_conn_info structure gives information about what features are supported
    by FUSE, and can be used to request certain capabilities (see below for more
    information). The return value of this function is available to all file
    operations in the private_data field of fuse_context. It is also passed as a
    parameter to the destroy() method.

    """

    def __init__(self, source):
        self.source = source

    def destroy(self, path):
        """Clean up any resources used by the filesystem.

        Called when the filesystem exits.

        """
        pass

    def _full_path(self, partial):
        """Calculate full path for the mounted file system.

          .. note::

            This isn't the same as the full path for the underlying file system.
            As such, you can't use os.path.abspath to calculate this, as that
            won't be relative to the mount point root.

        """
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.source, partial)
        return path

    @logged
    def access(self, path, mode):
        print("#### access", path, mode)
        """Access a file.

        This is the same as the access(2) system call. It returns -ENOENT if
        the path doesn't exist, -EACCESS if the requested permission isn't
        available, or 0 for success. Note that it can be called on files,
        directories, or any other object that appears in the filesystem. This
        call is not required but is highly recommended.

        """
        full_path = self._full_path(path)
        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)

    @logged
    def get_lstat_for_path(self, path):
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                                                        'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

    @logged
    def match_tag(self, path):
        # this is a router that will search for a file that has the tag in its name, and will return the file that most closely matches the tag
        if ("art:" in path):
            print("art: found")
            # try to split by , and if it fails, then take anything after the comma
            try:
                tags = path.split("/art:")[1].split(",")
            except:
                tags = [path.split("/art:")[1]]
            print("tags:", tags)
            possible_files = os.listdir(self.source)
            for file in possible_files:
                if all(tag in file for tag in tags):
                    path = file
        return path

    @logged
    def getattr(self, path, fh=None):
        print("#### getattr", path, fh)

        #  if you just look in the directory, its fine
        # if you get something that starts with degruchy_, then check what the rest of the filename is
        #  if the filename contains a , then we need to look and see if any images in the directory contain a _
        #  if they do, then we need to split the filename by , and split the directory listing by _
        # then do a match between each of the split parts and the images in the directory
        # we then return whichever matches most closely
        path = self.match_tag(path)

        return self.get_lstat_for_path(path)

        """Return file attributes.

        The "stat" structure is described in detail in the stat(2) manual page.
        For the given pathname, this should fill in the elements of the "stat"
        structure. If a field is meaningless or semi-meaningless (e.g., st_ino)
        then it should be set to 0 or given a "reasonable" value. This call is
        pretty much required for a usable filesystem.
        """

    @ logged
    def readdir(self, path, fh):
        print("#### readdir", path, fh)
        """Read a directory.

        Return one or more directory entries (struct dirent) to the caller.
        This is one of the most complex FUSE functions. It is related to, but
        not identical to, the readdir(2) and getdents(2) system calls, and the
        readdir(3) library function. Because of its complexity, it is described
        separately below. Required for essentially any filesystem, since it's
        what makes ls and a whole bunch of other things work.

        """
        full_path = self._full_path(path)

        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    @ logged
    def statfs(self, path):
        print("#### statfs", path)
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
                                                         'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
                                                         'f_frsize', 'f_namemax'))

    @ logged
    def open(self, path, flags):
        print("#### open", path, flags)
        path = self.match_tag(path)

        """Open a file.

        Open a file. If you aren't using file handles, this function should
        just check for existence and permissions and return either success or
        an error code. If you use file handles, you should also allocate any
        necessary structures and set fi->fh. In addition, fi has some other
        fields that an advanced filesystem might find useful; see the structure
        definition in fuse_common.h for very brief commentary.

        """
        full_path = self._full_path(path)
        return os.open(full_path, flags)

    @ logged
    def read(self, path, length, offset, fh):
        print("#### read", path, length, offset, fh)
        """Read from a file.

        Read size bytes from the given file into the buffer buf, beginning
        offset bytes into the file. See read(2) for full details. Returns the
        number of bytes transferred, or 0 if offset was at or beyond the end of
        the file. Required for any sensible filesystem.

        """
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    @ logged
    def flush(self, path, fh):
        print("#### flush", path, fh)
        """Flush buffered information.

        Called on each close so that the filesystem has a chance to report
        delayed errors. Important: there may be more than one flush call for
        each open. Note: There is no guarantee that flush will ever be called
        at all!

        """
        return os.fsync(fh)

    @ logged
    def release(self, path, fh):
        print("#### release", path, fh)
        """Release is called when FUSE is done with a file.

        This is the only FUSE function that doesn't have a directly
        corresponding system call, although close(2) is related. Release is
        called when FUSE is completely done with a file; at that point, you can
        free up any temporarily allocated data structures. The IBM document
        claims that there is exactly one release per open, but I don't know if
        that is true.

        """
        return os.close(fh)


if __name__ == '__main__':

    # add arguments as optional, with a default
    parser = argparse.ArgumentParser()
    parser.add_argument("mountpoint", help="the mountpoint where the files will be available",
                        default='mountpoint/', nargs='?')
    # optional argument
    parser.add_argument("source", help="the source directory where the files will be taken from",
                        default='source_folder/', nargs='?')
    args = parser.parse_args()

    print("starting")
    print("mountpoint", args.mountpoint)
    print("source", args.source)

    FUSE(Passthrough(source=args.source),
         args.mountpoint, foreground=True)
