# This file is part of EbookLib.
# Copyright (c) 2013 Borko Jandras <aerkalov@gmail.com>
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

from struct import Struct, unpack, pack
from cStringIO import StringIO


################################################################################
# Binary data parsing.
#

PALM_DATABASE_HEADER_STRUCT = Struct("> 32s 2H 10I H")

PALM_DATABASE_HEADER_KEYS = (
    "name", "attributes", "version",
    "creation_date", "modification_date", "last_backup_date",
    "modification_number", "app_info_id", "sort_info_id",
    "type", "creator", "unique_id_seed", "next_record_list_id",
    "number_of_records"
)

PALM_DATABASE_RECORD_STRUCT = Struct("> I B 3p")

PALM_DATABASE_RECORD_KEYS = (
    "record_data_offset", "record_attributes", "unique_id"
)

PALMDOC_HEADER_STRUCT = Struct("> 2H I 4H")

PALMDOC_HEADER_KEYS = (
    "compression", "unused", "text_length",
    "record_count", "record_size",
    "encryption_type", "unknown"
)

MOBI_HEADER_STRUCT = Struct("> 4s 28I 32p 5I 8p 2H 5I 8p 6I")

MOBI_HEADER_KEYS = (
    "identifier", "header_length", "mobi_type", "text_encoding", "unique_id",
    "file_version", "ortographic_index", "inflection_index", "index_names",
    "index_keys", "extra_index0", "extra_index1", "extra_index2",
    "extra_index3", "extra_index4", "extra_index5", "first_nonbook_index", 
    "full_name_offset", "full_name_length", "locale",
    "input_language", "output_language", "min_version", "first_image_index",
    "huffman_record_offset", "huffman_record_count",
    "huffman_table_offset", "huffman_record_length",
    "exth_flags", "unknown1", "unknown2",
    "drm_offset", "drm_count", "drm_size", "drm_flags", "unknown3",
    "first_content_record_number", "last_content_record_number", "unknown4",
    "fcis_record_number", "fcis_record_count",
    "flis_record_number", "flis_record_count",
    "unknown5", "unknown6",
    "first_compilation_data_section_count", "number_of_compilation_data_sections",
    "unknown7", "extra_record_data_flags", "indx_record_offset",
)

EXTH_HEADER_STRUCT = Struct("> 4s 2i")

EXTH_HEADER_KEYS = (
    "identifier", "header_length", "record_count"
)

EXTH_RECORD_STRUCT = Struct("> 2I")

EXTH_RECORD_KEYS = (
    "record_type", "record_length"
)


def parse_palm_database_header(src):
    values = unpack_struct(PALM_DATABASE_HEADER_STRUCT, src)
    return dict(zip(PALM_DATABASE_HEADER_KEYS, values))

def parse_palm_database_record(src):
    values = unpack_struct(PALM_DATABASE_RECORD_STRUCT, src)
    return dict(zip(PALM_DATABASE_RECORD_KEYS, values))

def parse_palmdoc_header(src):
    values = unpack_struct(PALMDOC_HEADER_STRUCT, src)
    return dict(zip(PALMDOC_HEADER_KEYS, values))

def parse_mobi_header(src):
    values = unpack_struct(MOBI_HEADER_STRUCT, src)
    return dict(zip(MOBI_HEADER_KEYS, values))

def parse_exth_header(src):
    values = unpack_struct(EXTH_HEADER_STRUCT, src)
    return dict(zip(EXTH_HEADER_KEYS, values))

def parse_exth_record(src):
    values = unpack_struct(EXTH_RECORD_STRUCT, src)
    return dict(zip(EXTH_RECORD_KEYS, values))


################################################################################
# Utilities.
#

def unpack_struct(struct, src):
    return struct.unpack(src.read(struct.size))


def tell_size(file):
    import os
    curr = file.tell()
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(curr, os.SEEK_SET)
    return size


def calc_padding(length, align):
    return (align - (length % align)) % align


################################################################################
# Compression
#

def palmdoc_decompress(src, dst, size):
    """Decompression for PalmDOC LZ77 compression method.
    """

    def decode_byte(c):
        return unpack("B", c)[0]
    def decode_word(s):
        b1, b2 = unpack("2B", s)
        return (b1 << 8) | (b2 & 0xFF)

    class Output:
        def __init__(self, dst):
            self.dst = dst
            self.hist = ""
            self.size = 0

        def write(self, s):
            self.dst.write(s)
            self.hist += s
            self.size += len(s)

        def write_match(self, distance, length):
            while length > 0:
                self.write(self.hist[-distance])
                length -= 1

    output = Output(dst)

    while output.size < size:
        c = src.read(1)
        if not c:
            break
        elif c == "\x00":
            output.write(c)
        elif c <= "\x08":
            count = decode_byte(c)
            while count > 0:
                output.write(src.read(1))
                count -= 1
        elif c <= "\x7F":
            output.write(c)
        elif c <= "\xBF":
            word = decode_word(c + src.read(1))
            dist = (word & 0x3FFF) >> 3
            leng = (word & 0x0007) + 3
            output.write_match(dist, leng)
        else:
            output.write(" " + pack("B", ord(c) ^ 0x80))

    return output.size


################################################################################
# Reader
#

class MobiReader(object):
    """Reader and parser for Mobipocket (KF7) files."""

    def __init__(self, file_name):
        self.text_length = 0
        with file(file_name, "rb") as src:
            self.__load(src)


    def __load(self, src):
        self.pdb_header = parse_palm_database_header(src)
        self.pdb_records = [parse_palm_database_record(src) for _ in xrange(self.pdb_header["number_of_records"])]

        for i in xrange(len(self.pdb_records)):
            self.__load_record(src, i)


    def __load_record(self, src, index):
        offset = self.pdb_records[index]["record_data_offset"]

        if index+1 < len(self.pdb_records):
            size = self.pdb_records[index+1]["record_data_offset"] - offset
        else:
            size = tell_size(src) - offset

        src.seek(offset)
        buff = src.read(size)

        if index == 0:
            self.__load_record0(buff)
        elif index < self.mobi_header["first_nonbook_index"]:
            self.__load_book_record(buff, index)
        else:
            self.__load_nonbook_record(buff, index)


    def __load_record0(self, buff):
        src = StringIO(buff)

        self.palmdoc_header = parse_palmdoc_header(src)

        if len(buff) - src.tell() >= MOBI_HEADER_STRUCT.size:
            self.mobi_header = parse_mobi_header(src)

        if len(buff) - src.tell() >= EXTH_HEADER_STRUCT.size:
            self.exth_header = parse_exth_header(src)
            for i in xrange(self.exth_header["record_count"]):
                exth_record = parse_exth_record(src)
                data_size = exth_record["record_length"] - 8
                print exth_record, src.read(data_size)
            #padding_size = calc_padding(exth_header["header_length"], 4)
            #src.read(padding_size)


    def __load_book_record(self, buff, index):
        left = self.palmdoc_header["text_length"] - self.text_length
        size = min(left, self.palmdoc_header["record_size"])
        dst = file("record%04d.bin" % (index, ), "w")
        palmdoc_decompress(StringIO(buff), dst, size)
        self.text_length += size

    def __load_nonbook_record(self, buff, index):
        dst = file("record%04d.bin" % (index, ), "w")
        dst.write(buff)
