<h1 align="center">Imgur -> 📁</h1>
<p align="center">Download Imgur albums and images to desired folder with one command.</p>

## Example usage

As mentioned above, the base command is `itf` or `imgurtofolder`. For the remainder of the readme, we'll be using `itf` as the base command.

*Example URLs are non-affiliated with the Imgur-To-Folder project.*

```bash
$ itf https://imgur.com/gallery/IhX0P # Download Galleries
$ itf https://i.imgur.com/4clqUdj.jpeg # Download direct images
```

## Dependencies

Tested with:

- `Python` >= 3.9
- `pip` >= 20.3.0

## Installation:

Start by cloning and installing the package using [`git`](https://git-scm.com/) and [`pip`](https://pypi.org/project/pip/).

```bash
$ git clone https://github.com/santosderek/Imgur-To-Folder
$ cd Imgur-To-Folder
$ pip install .
```

The package can be ran using included console script entrypoints. The entrypoint command is either `itf` or `imgurtofolder`:

```bash
$ itf -h
usage: itf [-h] [--folder PATH] [--change-default-folder PATH] [--download-favorites USERNAME] [--oldest] [--download-account-images USERNAME] [--max-downloads NUMBER_OF_MAX] [--start-page STARTING_PAGE] [--list-all-favorites USERNAME] [--print-download-path]
           [--overwrite] [--sort {time,top}] [--window {day,week,month,year,all}] [-v]
           [URLS ...]

Download images off Imgur to a folder of your choice!

positional arguments:
  URLS                  Automatically detect urls

optional arguments:
  -h, --help            show this help message and exit
  --folder PATH, -f PATH
                        Change desired folder path
  --change-default-folder PATH
                        Change the default desired folder path
  --download-favorites USERNAME, -df USERNAME
                        Username to download favorites of. Default: latest
  --oldest              Sort favorites by oldest.
  --download-account-images USERNAME, -dai USERNAME
                        Download account images to folder
  --max-downloads NUMBER_OF_MAX
                        Specify the max number of favorites to download
  --start-page STARTING_PAGE
                        Specify the starting page number for fravorites
  --list-all-favorites USERNAME, -lf USERNAME
                        List all favorites of a specified user
  --print-download-path
                        Print default download path.
  --overwrite           Write over existing content. (Disables skipping.)
  --sort {time,top}     How to sort subreddit time duration.
  --window {day,week,month,year,all}
                        Window of time for the sort method when using subreddit links. (Append "--sort top")
  -v, --verbose         Enables debugging output.
```

After pip installing the package, run the `itf` command where you'll be prompted for a `client_id`. Ignore this for now, but don't leave setup.

Next, either login to, or create an Imgur account at http://imgur.com/.

Now go to https://api.imgur.com/oauth2/addclient and create a new application using the following configuration:

| Config item | Expected value |
| ----------- | -------------- |
| Application Name | name of your choice |
| Authorization Type | OAuth 2 Authorization without a callback URL |
| Application website | \<blank\> |
| Email | Your email |
| Description | Any description you want to keep |


Once completed, you'll be given a `client_id` and `client_secret`. Head back to the terminal and paste these values where prompted.

Lastly, you should be prompted for a download path. Give the path you would like to use as default when downloading images.

Congrats! It's installed. Now you can run the `itf` or `imgurtofolder` to start downloading!

## Authentication Setup For Account Access (Only needed to download favorites)

To access your favorites, you must first permit this application to access your account. Again, this application does not store user name or passwords. This is the purpose of OAuth.

In order to do so, run either the `itf --list-all-favorites [username]` command, or the `itf --download-favorites [username]` command with your username replacing `[username]`.

A message will appear asking the user to visit a specified url and log in. This page takes you to Imgur to authenticate Imgur-To-Folder, and allow the program to view your favorites.

After logging in, you will be redirected back to the Imgur home page, though, your url address bar will contain new arguments. The url will now look like the url below:

`https://imgur.com/?state=authorizing#access_token={access_token_here}&expires_in={integer_here}&token_type=bearer&refresh_token={refresh_token_here}&account_username={your_username_here}&account_id={your_id_here}`

Paste in the redirected url located in the address bar, back into the terminal / cmd window to complete the authentication process.

You should now be able to list and download your Imgur favorites.

This step will no longer be needed for future favorites / account downloads after install.

## Imgur Rate Limiting.

"The Imgur API uses a credit allocation system to ensure fair distribution of capacity. Each application can allow approximately 1,250 uploads per day or approximately 12,500 requests per day. If the daily limit is hit five times in a month, then the app will be blocked for the rest of the month."

\- [Imgur Offical Documentation](https://apidocs.imgur.com/)

## Clarification

*Imgur-To-Folder does NOT store any username or password data. This is what the client_id and client_secret are for.*

*Though, Imgur themselves will ask you to verify that you want to allow my program to use your account info.*

*ALL sensitive data does NOT go to me in anyway, shape, or form.*
