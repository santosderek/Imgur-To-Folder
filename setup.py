from setuptools import setup, find_packages

setup(name='ImgurToFolder',
      version='0.2',
      description='Imgur Downloader to a folder of your choice.',
      author='Derek Santos',
      license='The MIT License (MIT)',
      url='https://github.com/santosderek/Imgur-To-Folder/',
      packages=['imgurtofolder'],
      scripts=['ImgurToFolder/__main__.py',
               'ImgurToFolder/__init__.py',
               'ImgurToFolder/config.py',
               'ImgurToFolder/imgur_downloader.py'],
      entry_points={
          'console_scripts':
              ['imgurtofolder = imgurtofolder.__main__:main',
               'itf = imgurtofolder.__main__:main']
      },
      install_requires=[
          'requests',
          'imgurpython==1.1.7'
      ]
      )
