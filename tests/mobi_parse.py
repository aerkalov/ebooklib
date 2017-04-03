
import sys

from ebooklib import mobi


if __name__ == "__main__":
    file_path = sys.argv[1]
    reader = mobi.MobiReader(file_path)
    print reader.pdb_header
    print reader.palmdoc_header
    print reader.mobi_header
    print reader.exth_header
