# Imgur-To-Folder
Download Imgur albums and images to desired folder

### How to install:

Either download the repository from the green 'Clone or download' button above, or (with git installed) copy and paste the commands bellow.

***Repository developed using Python 3***

    git clone https://github.com/santosderek/Imgur-To-Folder
    cd Imgur-To-Folder
    python setup.py install

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
