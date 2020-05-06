from setuptools import setup, find_packages
import sys

setup(name='ImgurToFolder',
      version='0.9.1',
      description='Imgur Downloader to a folder of your choice.',
      author='Derek Santos',
      license='Apache v2',
      url='https://github.com/santosderek/Imgur-To-Folder/',
      packages=['imgurtofolder'],
      scripts=['imgurtofolder/__main__.py',
               'imgurtofolder/imgur_downloader.py',
               'imgurtofolder/imgur.py',
               'imgurtofolder/logs.py',
               'imgurtofolder/configuration.py'],
      entry_points={
          'console_scripts':
              ['imgurtofolder=imgurtofolder.__main__:main',
               'itf=imgurtofolder.__main__:main']
      },
      package_data={},
      install_requires=[
          'requests'
      ]
      )
