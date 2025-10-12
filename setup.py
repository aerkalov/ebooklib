import io

from setuptools import setup


def read(path):
    with io.open(path, mode="r", encoding="utf-8") as fd:
        content = fd.read()
        return content


setup(
    name='EbookLib',
    version='0.20',
    author='Aleksandar Erkalovic',
    author_email='aerkalov@gmail.com',
    packages=['ebooklib', 'ebooklib.plugins'],
    url='https://github.com/aerkalov/ebooklib',
    project_urls={
        'Documentation': 'https://ebooklib.readthedocs.io',
        'Source': 'https://github.com/aerkalov/ebooklib',
        'Bug Tracker': 'https://github.com/aerkalov/ebooklib/issues'
    },
    license='GNU Affero General Public License',
    description='Ebook library which can handle EPUB2/EPUB3 and Kindle format',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    keywords=['ebook', 'epub', 'kindle'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    python_requires=">=2.7",
    install_requires=[
        "lxml",
        "six",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
            "sphinx",
        ],
        "test": [
            "pytest",
            "pytest-cov",
        ],
        "docs": [
            "sphinx",
        ],
    },
)

