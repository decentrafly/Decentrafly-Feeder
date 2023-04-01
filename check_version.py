#!/usr/bin/env python3
import sys


def check():
    if not sys.version_info >= (3, 7):
        print("Requires at least python 3.7")
        exit(1)
