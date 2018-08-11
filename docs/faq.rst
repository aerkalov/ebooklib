Frequently asked questions
==========================

How can I contribute?
---------------------

Easily! We don't have any special procedure for contributions. Just send us bug reports, suggestions or Pull Requests!

* Find bugs and report them here - https://github.com/aerkalov/ebooklib/issues
* Have a suggestions or idea for a feature? Write it here - https://github.com/aerkalov/ebooklib/issues
* Clone and send us Pull Requests - https://github.com/aerkalov/ebooklib/

Read and save does not work
---------------------------

At the moment you can not use ebooklib to read EPUB file, write it down using ebooklib and expect to get
file identical to the original. This is because ebooklib is opinionated when it comes to directory names,
content it saves and etc. Different EPUB files will place style sheet files, images, fonts and html files to
different directories than ebooklib. Ebooklib is also trying to produce valid EPUB3 output files, which is not
always the case with all input files. A lot of times input files will not pass epubcheck validation.

Because of that we we suggest that you read EPUB file using ebooklib, create new book instance using ebooklib and
transfer only things you care about. It is also up to you to change the paths for the links inside
(to style sheets, images and other html files). When you are done just write it down.

What happened to the MOBI support?
----------------------------------

We used to have branch with basic MOBI support. We stopped working on it as for our workflow KindleGen app
(converting EPUB->MOBI) was more than enough and we never needed to parse MOBI files.