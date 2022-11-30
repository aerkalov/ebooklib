# This file is part of EbookLib.
# Copyright (c) 2013 Aleksandar Erkalovic <aerkalov@gmail.com>
#
# EbookLib is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# EbookLib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with EbookLib.  If not, see <http://www.gnu.org/licenses/>.

# Version of ebook library

VERSION = (0, 18, 1)

# LIST OF POSSIBLE ITEMS
ITEM_UNKNOWN = 0
ITEM_IMAGE = 1
ITEM_STYLE = 2
ITEM_SCRIPT = 3
ITEM_NAVIGATION = 4
ITEM_VECTOR = 5
ITEM_FONT = 6
ITEM_VIDEO = 7
ITEM_AUDIO = 8
ITEM_DOCUMENT = 9
ITEM_COVER = 10
ITEM_SMIL = 11

# EXTENSION MAPPER
EXTENSIONS = {ITEM_IMAGE: ['.jpg', '.jpeg', '.gif', '.tiff', '.tif', '.png'],
              ITEM_STYLE: ['.css'],
              ITEM_VECTOR: ['.svg'],
              ITEM_FONT: ['.otf', '.woff', '.ttf'],
              ITEM_SCRIPT: ['.js'],
              ITEM_NAVIGATION: ['.ncx'],
              ITEM_VIDEO: ['.mov', '.mp4', '.avi'],
              ITEM_AUDIO: ['.mp3', '.ogg'],
              ITEM_COVER: ['.jpg', '.jpeg', '.png'],
              ITEM_SMIL: ['.smil']
              }
