# Imgur-To-Folder
Download Imgur albums and images to desired folder

[Gif of an example](https://gfycat.com/EvilHeftyGavial)

***

### Updates:
*Updated with ability to download without the use of -a or -i. It should automatically detect.*

*Updated with ability to download all favorited within your account.*

*There is now .gifv imgur link support.*

### How to install:

*Repository developed using Python 3*

*Copy repository from github:*


    git clone https://github.com/santosderek/Imgur-To-Folder
    cd Imgur-To-Folder

*Create an Imgur account at http://imgur.com/*

*Next go to https://api.imgur.com/oauth2/addclient and create a new application using a name of your choice, and the authorization type of:*

* OAuth 2 Authorization without a callback URL

*Complete the rest of the form.*

*Within * `ImgurToFolder/config.json` add in your CLIENT_ID and CLIENT_SECRET found on your http://imgur.com/account/settings/apps page.*

*Next within the command-line type: (and within the Imgur-To-Folder folder)*

    python3 setup.py install

*Congrats! It's installed. Now you can proceed bellow*

***

### How to use:
Base command:

    imgurToFolder

#### Following commands can be used:
***Help page***

    imgurToFolder --help

***Automatic Url Detection***

*Automatically downloads Imgur links without user specifically declaring the imgur type.*

    imgurtofolder [urls]

***Change folder path to download***

    imgurToFolder --folder FOLDER_PATH_HERE | OR | imgurToFolder --f  FOLDER_PATH_HERE

***Specifically download album/gallery using album url***

    imgurToFolder --album  ALBUM_URL_HERE | OR | imgurToFolder --a  ALBUM_URL_HERE

***Specifically download single image using image url***

*--image and -i command are used for i.imgur.com links*

    imgurToFolder --image  IMAGE_URL_HERE | OR | imgurToFolder --i  IMAGE_URL_HERE

***List First 60 favorited Imgur links within your profile***

*Please see below for authenticating setup.*

    imgurToFolder --list-all-favorites [username] | OR | imgurToFolder -lf [username]

***Download latest 60 favorited Imgur links within your profile***

*Please see below for authenticating setup.*

    imgurToFolder --download-latest-favorites [username] | OR | imgurToFolder -df [username]

### Authentication Setup For Account Access (Only needed to download favorites)

To access your favorites, you must first permit this application to access your account.

In order to do so, run either the `imgurToFolder --list-all-favorites [username]` command or the `imgurToFolder --download-latest-favorites [username]` command with your username replacing `[username]`.

A message will appear asking the user to visit a specified url and log in. This page takes you to Imgur to authenticate Imgur-To-Folder, and allow the program to view your favorites.

After logging in, you will be redirected back to the Imgur home page, though, your url address bar will contain new arguments. The url will now look like the url below:

`https://imgur.com/?state=authorizing#access_token={access_token_here}&expires_in={integer_here}&token_type=bearer&refresh_token={refresh_token_here}&account_username={your_username_here}&account_id={your_id_here}`

Paste in the redirected url located in the address bar, back into the terminal / cmd window to complete the authentication process.

You should now be able to list and download your Imgur favorites.

This step will no longer be needed for later favorites downloads. 

### Imgur Rate Limiting.

"The Imgur API uses a credit allocation system to ensure fair distribution of capacity. Each application can allow approximately 1,250 uploads per day or approximately 12,500 requests per day. If the daily limit is hit five times in a month, then the app will be blocked for the rest of the month."

\- [Imgur Offical Documentation](https://apidocs.imgur.com/)

#### Warning

imgur.com/r/\*** links are not supported yet! - This will just download the HTML code off the Imgur page.

### Clarification

*Imgur-To-Folder does NOT store any username or password data. This is what the client_id and client_secret are for.*

*Though, Imgur themselves will ask you to verify that you want to allow my program to use your account info.*

*ALL sensitive data does NOT go to me in anyway, shape, or form.*
