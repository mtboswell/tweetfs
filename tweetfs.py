#!/usr/bin/env python
"""
TweetFS : A FUSE based filesystem that displays tweets as files
in a twitter user's directory.

Author:
    Sreejith K <sreejithemk@gmail.com>
    http://semk.in
    Copyright (c) 2009, Sreejith K

Licensed under GNU GPL v3 or later. Refer COPYING for more.
"""

from __future__ import with_statement

from errno import EACCES
from os.path import realpath
from sys import argv, exit
import threading

import os
import twitter
from time import sleep

from fuse import FUSE, Operations, LoggingMixIn

USERNAME            = 'twittfs'
PASSWD              = 'ezpasswd'
UPDATE_INTERVAL     = 600
USER_TWEETS         = 10
FRIEND_TWEETS       = 10


def tweetfs_update(root, api):
    """
    This will update the TweetFS filesystem with new tweets.
    """

    # Setup the user's home directory
    home_dir = root + '/' + USERNAME
    if not os.path.exists(home_dir):
        print 'Creating directory', home_dir
        os.mkdir(home_dir)

    # Get the user's tweets
    try:
        tweets = api.GetUserTimeline(USERNAME, count=USER_TWEETS)
    except Exception:
        print 'Problem connecting to twitter. Safe to Ignore'
        tweets = []

    # Write the user's tweets into regular files. Filename will be the tweet id
    for tweet in tweets:
        tweet_file = home_dir + '/' + str(tweet.id)
        if not os.path.exists(tweet_file):
            print 'Writing tweets in', tweet_file
            tf = open(tweet_file, 'a+')
            tf.write(tweet.text + '\n')
            tf.close()

    try:
        friends = api.GetFriends()
    except Exception:
        'Problem connecting to Twitter. Safe to Ignore.'
        friends = []

    # Setup user's friend's directories
    for friend in friends:
        if not os.path.exists(root + '/' + friend._screen_name):
            print 'Creating directory', root + '/' + friend._screen_name
            os.mkdir(root + '/' + friend._screen_name)
            
        # Get friend's tweets
        try:
            tweets = api.GetUserTimeline(friend._screen_name, count=FRIEND_TWEETS)
        except Exception:
            print 'Problem connecting to Twitter. Safe to Ignore.'
            tweets = []

        # Write friend's tweets into regular files inside the friend's directory
        for tweet in tweets:
            tweet_file = root + '/' + friend._screen_name + '/' + str(tweet.id)
            if not os.path.exists(tweet_file):
                print 'Writing tweets in', tweet_file
                tf = open(tweet_file, 'a+')
                tf.write(tweet.text.encode('ascii', 'ignore') + '\n')
                tf.close()

def update_scheduler(root, api):
    """
    This method calls tweetfs_update regularly.
    """

    while True:
        tweetfs_update(root, api)
        sleep(UPDATE_INTERVAL)

class TweetFS(LoggingMixIn, Operations):    
    def __init__(self, root):
        self.root = realpath(root)
        self.rwlock = threading.Lock()
        self.api = twitter.Api(username=USERNAME, password=PASSWD)
        
        # Start a thread that populate the directories with tweets.
        self.update_thread = threading.Thread(target=update_scheduler, 
                name='update-thread', args=(self.root, self.api))
        self.update_thread.setDaemon(True)
        self.update_thread.start()
    
    def __call__(self, op, path, *args):
        return super(TweetFS, self).__call__(op, self.root + path, *args)
    
    def access(self, path, mode):
        if not os.access(path, mode):
            raise OSError(EACCES, '')
    
    chmod = None
    chown = os.chown
    
    def create(self, path, mode):
        if os.path.dirname(path).split('/')[-1] == USERNAME:
            return os.open(path, os.O_WRONLY | os.O_CREAT, mode)
        else:
            raise OSError(EACCES, '')
    
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
    
    def mkdir(self, path, mode):
        user = os.path.basename(path)
        print 'Now following', user

        try:
            self.api.CreateFriendship(user=user)
            os.mkdir(path, mode)
        except Exception:
            print 'Error occured while following', user
    
    mknod = os.mknod
    open = os.open
        
    def read(self, path, size, offset, fh):
        with self.rwlock:
            os.lseek(fh, offset, 0)
            return os.read(fh, size)
    
    def readdir(self, path, fh):
        return ['.', '..'] + os.listdir(path)


    readlink = os.readlink
    
    def release(self, path, fh):
        return os.close(fh)
        
    def rename(self, old, new):
        return os.rename(old, self.root + new)
    
    def rmdir(self, path):
        user = os.path.basename(path)
        try:
            print 'Removing %s from friends list' % user
            self.api.DestroyFriendship(user=user)
            os.rmdir(path)
        except Exception:
            print 'Error removing friendship'
    
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
    
    def unlink(self, path):
        user_or_id = os.path.basename(path)

        if os.path.isdir(path):
            try:
                print 'Removing %s from friends list' % user
                self.api.DestroyFriendship(user=user_or_id)
                os.unlink(path)
            except Exception:
                'Error removing friendship'
        else:
            if os.path.dirname(path).split('/')[-1] == USERNAME:
                try:
                    self.api.DestroyStatus(id=user_or_id)
                except Exception:
                    'Error removing status'
                os.unlink(path)
            else:
                os.unlink(path)
        
    utimens = os.utime
    
    def write(self, path, data, offset, fh):
        with self.rwlock:
            os.lseek(fh, offset, 0)
            user = os.path.dirname(path).split('/')[-1]

            # Update the user's status
            if user == USERNAME:
                try:
                    status = self.api.PostUpdate(data)
                except UnicodeDecodeError:
                    print 'Your Message cannot be encoded. Perhaps it contains non-ASCII characters'
            # Post a Direct Message to friend
            else:
                self.api.PostDirectMessage(user=user, text=data)
            return os.write(fh, data)
    

if __name__ == "__main__":
    if len(argv) != 3:
        print 'usage: %s <root> <mountpoint>' % argv[0]
        exit(1)
    fuse = FUSE(TweetFS(argv[1]), argv[2], foreground=True)
