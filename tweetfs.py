#!/usr/bin/env python

from __future__ import with_statement

from errno import EACCES
from os.path import realpath
from sys import argv, exit
from threading import Lock

import os
import twitter

from fuse import FUSE, Operations, LoggingMixIn

USERNAME    = 'sreejithemk'
PASSWD      = 'kesavan'


def tweetfs_update(root, api):
    """
    This will update the TweetFS filesystem with new tweets.
    """

    # Setup the user's home directory
    home_dir = root + '/' + USERNAME
    if not os.path.exists(home_dir):
        os.mkdir(home_dir)

    # Get the user's tweets
    tweets = twitter.Api().GetUserTimeline(USERNAME, count=10)

    # Write the user's tweets into regular files. Filename will be the tweet id
    for tweet in tweets:
        tweet_file = home_dir + '/' + str(tweet.id)
        if not os.path.exists(tweet_file):
            tf = open(tweet_file, 'a+')
            tf.write(tweet.text + '\n')
            tf.close()

    # Setup user's friend's directories
    for friend in api.GetFriends():
        if not os.path.exists(root + '/' + friend._screen_name):
            os.mkdir(root + '/' + friend._screen_name)
            
        # Get friend's tweets
        tweets = api.GetFriendsTimeline(user=friend.id, count=10)

        # Write friend's tweets into regular files inside the friend's directory
        for tweet in tweets:
            tweet_file = root + '/' + friend._screen_name + '/' + str(tweet.id)
            if not os.path.exists(tweet_file):
                tf = open(tweet_file, 'a+')
                tf.write(tweet.text.encode('ascii', 'ignore') + '\n')
                tf.close()


class TweetFS(LoggingMixIn, Operations):    
    def __init__(self, root):
        self.root = realpath(root)
        self.rwlock = Lock()
        self.api = twitter.Api(username=USERNAME, password=PASSWD)
        tweetfs_update(self.root, self.api)
    
    def __call__(self, op, path, *args):
        return super(TweetFS, self).__call__(op, self.root + path, *args)
    
    def access(self, path, mode):
        if not os.access(path, mode):
            raise OSError(EACCES, '')
    
    chmod = os.chmod
    chown = os.chown
    
    def create(self, path, mode):
        return os.open(path, os.O_WRONLY | os.O_CREAT, mode)
    
    def flush(self, path, fh):
        return os.fsync(fh)

    def fsync(self, path, datasync, fh):
        return os.fsync(fh)
                
    def getattr(self, path, fh=None):
        st = os.lstat(path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
            'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
    
    getxattr = None
    
    def link(self, target, source):
        return os.link(source, target)
    
    listxattr = None
    mkdir = os.mkdir
    mknod = os.mknod
    open = os.open
        
    def read(self, path, size, offset, fh):
        with self.rwlock:
            os.lseek(fh, offset, 0)
            return os.read(fh, size)
    
    def readdir(self, path, fh):
        #tweetfs_update(self.root, self.api)
        return ['.', '..'] + os.listdir(path)


    readlink = os.readlink
    
    def release(self, path, fh):
        return os.close(fh)
        
    def rename(self, old, new):
        return os.rename(old, self.root + new)
    
    rmdir = os.rmdir
    
    def statfs(self, path):
        stv = os.statvfs(path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))
    
    def symlink(self, target, source):
        return os.symlink(source, target)
    
    def truncate(self, path, length, fh=None):
        with open(path, 'r+') as f:
            f.truncate(length)
    
    unlink = os.unlink
    utimens = os.utime
    
    def write(self, path, data, offset, fh):
        with self.rwlock:
            os.lseek(fh, offset, 0)
            if os.path.basename(path) == USERNAME:
                api = twitter.Api(username=USERNAME, password=PASSWD, input_encoding='utf-8')
                try:
                    status = api.PostUpdate(data)
                except UnicodeDecodeError:
                    print 'Your Message cannot be encoded. Perhaps it contains non-ASCII characters'
            else:
                ss
            return os.write(fh, data)
    

if __name__ == "__main__":
    if len(argv) != 3:
        print 'usage: %s <root> <mountpoint>' % argv[0]
        exit(1)
    fuse = FUSE(TweetFS(argv[1]), argv[2], foreground=True)
