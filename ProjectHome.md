TweetFS is a FUSE filesystem written in Python that can manage twitter statuses of users as regular files. Users are also able to update the tweets by adding files to the user's directory. This will eventually update the user status on Twitter. If a new file is created in another user's folder, they will get it as a personal message.

This project makes use of python-twitter and fusepy modules for python.

**Usage**

Mount the filesystem by running

```
python tweetfs.py <root-dir> <mount-point>
```

where root-dir is an empty directory (will be updated with tweets soon) where you need to store the tweets. mount-point is an empty directory where you need to mount the virtual TweetFS filesystem. Always access the files through mount-point directory.

After the TweetFS, directories will get created for you and for your friends in Twitter. Tweets will appear in files inside the directories of each user. The filename will be the Tweet's internal ID.

To update your Twitter status just create a file with your status message in it under your directory. For eg: Suppose your twitter username is twittfs. To update your status do

```
cat "Just a simple tweet from TweetFS" > <mount-point>/twittfs/new_status
```

You can give any name for the new file created.

If you are creating a new file inside a friends directory, then he'll get the content as a Direct Personal Message. This is as simple as

```
cat "This is a direct message from twittfs" > <mount-point>/<friends-name>/direct_message
```

To delete your status message, Just delete the file you have created.
```
rm <mount-point>/twittfs/<status_to_be_deleted>
```

And if you want to follow someone, create a folder with their username. Say if you want to follow aplusk. Then do

```
mkdir <mount-point>/aplusk
```

For unfollowing a user, just delete his directory

```
rm -rf <mount-point>/<user_to_unfollow>
```

Thanks for trying out.

Sreejith K
http://semk.in