# Version of ebook library

VERSION = (0, 1, 0)

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

# EXTENSION MAPPER
EXTENSIONS = {ITEM_IMAGE: ['.jpg', '.jpeg', '.gif', '.tiff', '.tif', '.png'],
              ITEM_STYLE: ['.css'],
              ITEM_VECTOR: ['.svg'],
              ITEM_FONT: ['.otf', '.woff'],
              ITEM_SCRIPT: ['.js'],
              ITEM_NAVIGATION: ['.ncx'],
              ITEM_VIDEO: ['.mov', '.mp4', '.avi'],
              ITEM_AUDIO: ['.mp3', '.ogg']
              }
