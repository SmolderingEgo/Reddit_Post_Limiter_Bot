#!/usr/bin/env python3

import time
import praw
import inspect
import os.path  # this is for just checking for a db file
import sqlite3
import logging
from datetime import datetime, timedelta

# configure the logger
logging.basicConfig(filename='postlimit.log',
                    level=logging.INFO,
                    format='%(asctime)s %(message)s')


# User config
# --------------------------------------------------------------------
# Don't include the /r/
SUBREDDIT_NAME = 'BravenewbiesBeta'

# Set to false if you want it to enforce all posts
ONLY_LINKS = False

# Set this to the number of days between posts
POST_LIMIT = 1 # TODO
OVERRIDE_KEYWORD = "override"
# Comment that will be added to post before removal
# Note: If you change this comment the {variable}'s must remain as is.
# You can put them wherever you like but you cannot delete them or 
# change the variable name without altering the .format() call on lines 81-82
COMMENT = '''
--------
--------
From The Recruitment_Bot-

You have already posted in the past {post_limit} days, therefore your post
has been removed as it has broken the rules.

You have *{days_left}* days until you can post again.

Your last post is [here](https://www.reddit.com/comments/{subm_id}/).

--------

#####_I'm just a bot, if you think this is a mistake contact the [moderators](https://www.reddit.com/message/compose?to=%2Fr%2Fwowguilds)_ 
'''

# --------------------------------------------------------------------


def msg_mods(r, subm):
    msg = '''[This post](https://www.reddit.com/comments/{}) was flagged for
             removal but there was an error in processing it. Please take a look.'''

    print('Messaging mods...')
    r.send_message('/r/' + SUBREDDIT_NAME, 'Error with post removal', msg, captcha=None)


def log_removal(subm, entry):
    log_msg = '''
    /u/{}'s post was removed on {}. Their last post was on {}.
    It's been {} days since their last post.
    Link to last post: https://www.reddit.com/comments/{}/
    Link to post removed: {}
    '''

    last_post_date = datetime.fromtimestamp(float(entry[1]))
    last_post_id = entry[2]

    logging.info(log_msg.format(str(subm.author), datetime.utcnow().strftime('%c'),
                                last_post_date.strftime('%c'),
                                (datetime.utcnow() - last_post_date).days,
                                last_post_id, subm.permalink))

    return True


def comment_removal(submission, entry):
    # adds the post limit to their last post date and subtracts the current time
    # to get the current amount of days until they can post again
    last_post = datetime.fromtimestamp(float(entry[1]))
    days_left = ((last_post + timedelta(days=POST_LIMIT)) - datetime.utcnow()).days

    print('Adding commment...')
    submission.reply(COMMENT.format(post_limit=POST_LIMIT, days_left=days_left,
                                    subm_id=entry[2]))


def check_if_author_already_posted(author, submission, cur, reddit):
    print('Checking if author has posted in the last {} days...'.format(POST_LIMIT))
    subm_id = submission.id
    # fetch the author from the database
    cur.execute('SELECT * FROM authors WHERE name = ?', [author])
    entry = cur.fetchone()

    # if we couldn't get an entry then that have never posted, return false
    if entry is None:
        return False
    else:
        # if the current submission is the one we already have stored ignore it
        if entry[2] == subm_id:
            return False

        # if mod override, return True and keep post
        if check_if_mod_override(reddit, submission):
            return False

        # create a datetime object from the epoch timestamp of submission
        last_posted = datetime.fromtimestamp(float(entry[1]))
        # if their last post plus the post limit is greater than the current time
        # that means they have posted within the post limit.

        #debug
        print((last_posted + timedelta(days=POST_LIMIT)).date(), ">", datetime.utcnow().date())
        if (last_posted + timedelta(days=POST_LIMIT)).date() > datetime.utcnow().date():
            return True
        else:  # has posted but last post is older than the limit
            return False


def check_if_mod_override(reddit, submission):
    # get all mods
    mods = list(reddit.subreddit(SUBREDDIT_NAME).moderator())

    # get all comments
    all_comments = submission.comments.list()

    for comment in all_comments:
        print(comment)
        if comment.body.lower() == OVERRIDE_KEYWORD.lower() and comment.author in mods:
            return True

    return False


def remove_submission(submission, cur, r):
    print('Removing post...')

    # grab the most recent post stored in the db of the op of the submission
    cur.execute('SELECT * FROM authors WHERE name = ?', [str(submission.author)])
    entry = cur.fetchone()

    # if an entry could not be grabbed from the db, but the post was flagged
    # log the event then message the mods and don't remove the post
    if not entry:
        print('ERROR: {} was flagged for removal but couldn\'t find it in db.')
        logging.error('ERROR: {} was flagged for removal but could not find\
                       last post in db. Mods will be messaged.'.format(subm.permalink))
        msg_mods(submission, r)
        return  # exit the function instead of removing the post

    log_removal(submission, entry)  # log the event
    comment_removal(submission, entry)  # comment on the post to notify op of the removal
    submission.delete()  # then remove the post


def add_or_update_author(sql, cur, name, date, subm_id):
    print('Updating database...')
    cur.execute('SELECT * FROM authors where name = ?', [name])

    # if they already have an entry update it
    if cur.fetchone():
        cur.execute('UPDATE authors SET last_post = ?, subm_id = ? WHERE name = ?', [date, subm_id, name])
    else:  # if not just create it
        cur.execute('INSERT INTO authors VALUES(?, ?, ?)', [name, date, subm_id])
    sql.commit()
    print("Database updated")


def find_posts(reddit, sql, cur):
    print('Searching posts...')
    subreddit = reddit.subreddit(SUBREDDIT_NAME)

    # stream though all new submissions
    for submission in subreddit.stream.submissions():
        # Check if only links is True, and if the post is text just ignore it
        if ONLY_LINKS and submission.is_self:
            continue
        # Check if the post itself is older than the post limit, if so we can ignore it. Only checking Dates, not time
        if (datetime.fromtimestamp(submission.created) + timedelta(days=POST_LIMIT)).date() < datetime.utcnow().date():
            continue
        # Then we will check if the author has already posted in the past 5 days
        if check_if_author_already_posted(str(submission.author), submission, cur, reddit):
            remove_submission(submission, cur, reddit)  # if they have we will remove the post
        # If there is no record of the author posting, or it's been more than 30 days
        # we will create an entry for the author or update an authors entry
        else:
            add_or_update_author(sql, cur, str(submission.author), str(submission.created_utc), submission.id)


def format_var_str(dic):
    s = ''
    for var, val in dic.items():
        s += ('\t' * 8) + '{}: {}\n'.format(var, val)

    return s


def main():
    reddit = praw.Reddit(user_agent='Post_Limit_Enforcer v1.5 /u/cutety')

    # Setup/Load the database
    # First we have to check for old database file name
    sql = sqlite3.connect('PostLimitEnforcer.db')  # new version name

    cur = sql.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS authors(name TEXT, last_post TEXT, subm_id TEXT)')
    sql.commit()
    print('Database loaded.')

    # Main loop
    while True:
        try:
            find_posts(reddit, sql, cur)
        except Exception as e:
            print('ERROR: {}'.format(e))

            # log the error event with specific information from the traceback
            traceback_log = '''
            ERROR: {e}
            File "{fname}", line {lineno}, in {fn}
            Time of error: {t}

            Variable dump:

            {g_vars}
            {l_vars}
            '''
            # grabs the traceback info
            frame, fname, lineno, fn = inspect.trace()[-1][:-2]
            # dump the variables and get formated strings
            g_vars = 'Globals:\n' + format_var_str(frame.f_globals)
            l_vars = 'Locals:\n' + format_var_str(frame.f_locals)

            logging.error(traceback_log.format(e=e, lineno=lineno, fn=fn,
                                               fname=fname, t=time.strftime('%c'),
                                               g_vars=g_vars, l_vars=l_vars))

        print('Sleeping...')
        time.sleep(300)  # go to sleep for a little bit

if __name__ == '__main__':
    if not SUBREDDIT_NAME:
        print('Subreddit name has not been set.\nExiting...')
        exit(1)
    if type(POST_LIMIT) is not int or POST_LIMIT <= 0:
        print('The post limit must be a postive integer.\nExiting...')
        exit(1)

    main()
