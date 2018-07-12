# -*- coding: utf-8 -*-

from __future__ import print_function

class default_logger():

    @classmethod
    def critical(cls, s):
        print("CRITICAL:", s)

    @classmethod
    def error(cls, s):
        print("ERROR:", s)

    @classmethod
    def warning(cls, s):
        print("WARNING:", s)

    @classmethod
    def info(cls, s):
        print("INFO:", s)

    @classmethod
    def debug(cls, s):
        print("DEBUG:", s)

