# Imgur-To-Folder
Download Imgur albums and images to desired folder
***
### How to install:
***Copy repository from github:***

*Repository developed using Python 3*

    git clone https://github.com/santosderek/Imgur-To-Folder
    cd Imgur-To-Folder

*Create an Imgur account at http://imgur.com/*

*Next go to https://api.imgur.com/oauth2/addclient and create a new application using a name of your choice, and the authorization type of:*

***OAuth 2 Authorization without a callback URL***

*Complete the rest of the form.*

*Within ImgurToFolder/config.py add in your CLIENT_ID and CLIENT_SECRET found on your http://imgur.com/account/settings/apps page.*

*Next within the command-line type:*

    python setup.py install

*Congrats! It's installed. Now you can proceed bellow*

***

### How to use:
Base command:

    imgurToFolder

#### Following commands can be used:
***Help page***

    imgurToFolder --help

***Change folder path to download***

    imgurToFolder --folder FOLDER_PATH_HERE

***Download album/gallery using album url***

    imgurToFolder --album  ALBUM_URL_HERE

***Download single image using image url***

*--image and -i command are used for i.imgur.com links*

    imgurToFolder --image  IMAGE_URL_HERE


Example:
    *Download image of random cat I found*

    imgurToFolder --folder C:\Users\Apollo\Downloads -i http://i.imgur.com/aauKqQB.jpg

#### Warning

imgur.com/r/*** links are not supported yet! - This will just download the HTML code of the Imgur page.
