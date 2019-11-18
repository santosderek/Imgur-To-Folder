![Dyrenex Software](Dyrenex_Software.png)

# Imgur-To-Folder
Download Imgur albums and images to desired folder with one command.

![Gif of an example](https://giant.gfycat.com/AccurateHarmfulAmericanalligator.gif)

[Webm of an example](https://giant.gfycat.com/AccurateHarmfulAmericanalligator.webm)


---

### How to install:

*Repository developed using Python 3*

*Copy repository from github:*


    git clone https://github.com/santosderek/Imgur-To-Folder
    cd Imgur-To-Folder

*Create an Imgur account at http://imgur.com/ or log in if you have one already.*

*Next go to https://api.imgur.com/oauth2/addclient and create a new application using a name of your choice, and the authorization type of:*

* OAuth 2 Authorization without a callback URL

*Complete the rest of the form.*

*Within * `imgurtofolder/config.json` add in your CLIENT_ID and CLIENT_SECRET found on your http://imgur.com/account/settings/apps page.*

*Next within the command-line type: (and within the Imgur-To-Folder folder)*

    python3 setup.py install

*Congrats! It's installed. Now you can proceed bellow*

***

### How to use:
Base command:

    imgurtofolder

Or for simplicity, you can use:

    itf

*All commands below can be used with either base command.*

#### Following commands can be used:
***Help page***

    imgurtofolder --help

***Automatic Url Detection***

*Automatically downloads Imgur links without user specifically declaring the Imgur type, as opposed to earlier versions.*

    imgurtofolder [urls]

***Change folder path to download***

    imgurtofolder --folder FOLDER-PATH-HERE | OR | imgurtofolder -f  FOLDER-PATH-HERE

***Download all account images within your profile***

*Please see below for authenticating setup.*

    imgurtofolder --download-account-images | OR | imgurtofolder -dai

***List all favorited Imgur links within your profile***

*Please see below for authenticating setup.*

    imgurtofolder --list-all-favorites [username] | OR | imgurtofolder -lf [username]

***Download favorited Imgur links within your profile***

*Please see below for authenticating setup.*

*Download all favorites in order of latest.*

    imgurtofolder --download-latest-favorites [username] | OR | imgurtofolder -df [username]

*Download all favorites in order of oldest.*

    imgurtofolder --download-oldest-favorites [username] | OR | imgurtofolder -do [username]

*To limit number of favorites to download use `--max-favorites`:*

    imgurtofolder --download-latest-favorites [username] --max-favorites [maximum_number_of_favorites]

    [OR]

    imgurtofolder --download-oldest-favorites [username] --max-favorites [maximum_number_of_favorites]

*Example for latest 60 favorites*

    imgurtofolder --download-latest-favorites [username] --max-favorites 60

***Over-write existing files (disables skipping)***

*To over-write existing files use `--overwrite`*

    imgurtofolder [URLS] --overwrite

***Enable debugging output***

*To enable debugging output use `--verbose`*

    imgurtofolder [URLS] --verbose

### Authentication Setup For Account Access (Only needed to download favorites)

To access your favorites, you must first permit this application to access your account. Again, this application does not store user name or passwords. This is the purpose of OAuth.

In order to do so, run either the `imgurtofolder --list-all-favorites [username]` command, the `imgurtofolder --download-latest-favorites [username]` command, or the `imgurtofolder --download-oldest-favorites [username]` command with your username replacing `[username]`.

A message will appear asking the user to visit a specified url and log in. This page takes you to Imgur to authenticate Imgur-To-Folder, and allow the program to view your favorites.

After logging in, you will be redirected back to the Imgur home page, though, your url address bar will contain new arguments. The url will now look like the url below:

`https://imgur.com/?state=authorizing#access_token={access_token_here}&expires_in={integer_here}&token_type=bearer&refresh_token={refresh_token_here}&account_username={your_username_here}&account_id={your_id_here}`

Paste in the redirected url located in the address bar, back into the terminal / cmd window to complete the authentication process.

You should now be able to list and download your Imgur favorites.

This step will no longer be needed for future favorites / account downloads after install.

### Imgur Rate Limiting.

"The Imgur API uses a credit allocation system to ensure fair distribution of capacity. Each application can allow approximately 1,250 uploads per day or approximately 12,500 requests per day. If the daily limit is hit five times in a month, then the app will be blocked for the rest of the month."

\- [Imgur Offical Documentation](https://apidocs.imgur.com/)

### Changes

- Now currently using Imgur's RESTful API.
- Works with any form of Imgur link.
- Can now handle subreddit links.
- Takes less queries to get all images within album.
- Code is more relative, and not as absolute.
- No longer need to specify type.
- No longer using deprecated ImgurPython.
- No longer supports single images folder.

### Clarification

*Imgur-To-Folder does NOT store any username or password data. This is what the client_id and client_secret are for.*

*Though, Imgur themselves will ask you to verify that you want to allow my program to use your account info.*

*ALL sensitive data does NOT go to me in anyway, shape, or form.*
