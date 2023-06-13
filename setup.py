from setuptools import setup, find_packages
from pathlib import Path

setup(
    name='ImgurToFolder',
    version='0.11.0',
    description='Imgur Downloader to a folder of your choice.',
    author='Derek Santos',
    license='Apache v2',
    url='https://github.com/santosderek/Imgur-To-Folder/',
    package_dir={"": "src/"},
    packages=find_packages("src"),
    entry_points={
        'console_scripts':
        [
            'imgurtofolder=imgurtofolder.__main__:main',
            'itf=imgurtofolder.__main__:main'
        ]
    },
    package_data={},
    install_requires=Path('requirements.txt').read_text().splitlines(),
)
