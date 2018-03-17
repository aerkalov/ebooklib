#from distutils.core import setup
from setuptools import setup

setup(
    name = 'EbookLib',
    version = '0.15',
    author = 'Aleksandar Erkalovic',
    author_email = 'aerkalov@gmail.com',
    packages = ['ebooklib', 'ebooklib.plugins'],
    url = 'https://github.com/aerkalov/ebooklib',
    license = 'GNU Affero General Public License',
    description = 'Ebook library which can handle EPUB2/EPUB3 and Kindle format',
    long_description = open('README.md').read(),
    keywords = ['ebook', 'epub', 'kindle'],
    classifiers = [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    install_requires = [
       "lxml", "six"
    ]
)

