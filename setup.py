from setuptools import setup, find_packages

setup(name='ImgurToFolder',
      version='0.1',
      description='Imgur Downloader to a folder of your choice.',
      author='Derek Santos',
      license='The MIT License (MIT)',
      url='https://github.com/santosderek/Imgur-To-Folder/',
      packages=['imgurtofolder'],
      scripts=['ImgurToFolder/main.py',
               'ImgurToFolder/config.py',
               'ImgurToFolder/downloader.py'],
      entry_points={
          'console_scripts':
              ['imgurToFolder = main:main',
               'itf = main:main']
      },
      install_requires=[
          'requests',
          'imgurpython==1.1.7'
      ]
      )
