# -*- coding: utf-8 -*-
class FileError(Exception):
    """ Raised if the file cannot be read. """
    pass

class FiletypeError(FileError):
    """ Raised for unsupported filetypes. """
    pass
