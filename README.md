Post Limit Enforcer
===================

Installations
-------------

This script requires python 3, praw, and praw-oauth2util.

To install praw type in your command line:

    pip install praw

Reddit OAuth Setup
------------------

* Copy `praw.ini.template` and call it `praw.ini`
* [Go here on the account you want the bot to run on](https://www.reddit.com/prefs/apps/)
* Click on create a new app.
* Give it a name. 
* Select script from the radio buttons.
* Set the redirect uri to `http://127.0.0.1:65010/authorize_callback`
* After you create it you will be able to access the app key and secret.
* The **app key** is found here. Add this to the client_id variable in the praw.ini file.

![here](http://i.imgur.com/7ybI5Fo.png) (**Do not give out to anybody**) 

* And the **app secret** here. Add this to the client_secret variable in the praw.ini file.

![here](http://i.imgur.com/KkPE3EV.png) (**Do not give out to anybody**)

* add either refresh_token to praw.ini, or password and username of the account the bot is registered on and should use

Config
------
Set the SUBREDDIT_NAME variable to the name of the subreddit, don't include the /r/.

Set the POST_LIMIT variable to the number of days between posts users posts will be removed.

Set the OVERRIDE_KEYWORD variable to the keyword the mods can use to, ignore a post

Set the COMMENT variable to the comment you want the bot to reply with when it removes a post. *Note: If you change this comment, the `{variable}`'s must remain as is. You can put them wherever you like but you cannot delete them or hange the variable name without altering the `.format()` call on lines 81-82.*

License
-------

The MIT License (MIT)

Copyright (c) 2015 Nick Hurst

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
