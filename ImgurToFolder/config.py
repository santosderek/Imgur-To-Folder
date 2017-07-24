# ImgurToFolder Configuration
configuration = {
    # Client ID here
    'client_id':'',

    # Client Secret here
    'client_secret':'',

    # Refresh Token here.
    # If no refresh token, one could be generated for you by using
    # '--download-all-favorites' argument
    'refresh_token':'',

    # Path to destination folder.
    # If left alone, it will download to current folder
    # when application is running
    'download_folder_path':r'.',

    # This argument will put single images within a folder called
    # 'Single Images'. If you want this setting off replace True with False
    'single_images_folder':True
}
