#!/usr/bin/python3
from io import FileIO

class Decoder:
    FRAME_BYTE   = 26
    MODE_AC_BYTE = 49
    MODE_S_BYTE  = 50
    MODE_SL_BYTE = 51

    def __init__(self):
        self.current_frame = bytearray()
        self.frames = []
        self.last_byte = -1
        self.in_prefix = True
        self.seen_frame_byte = False

    def finalize_frame(self, b):
        if self.in_prefix:
            self.in_prefix = False
            print(len(self.current_frame))
        else:
            self.frames.append(self.current_frame)
        self.current_frame = bytearray([self.FRAME_BYTE, b])

    def read_escaped_byte(self, b):
        if b == self.FRAME_BYTE:
            self.current_frame.append(b)
            self.current_frame.append(b)
        elif (b == self.MODE_AC_BYTE
              or b == self.MODE_S_BYTE
              or b == self.MODE_SL_BYTE):
            self.finalize_frame(b)
        else:
            # RESET and ignore broken frame
            self.current_frame = bytearray()
            self.last_byte = -1
            self.in_prefix = True

    def read_byte(self, b):
        if self.seen_frame_byte:
            self.read_escaped_byte(b)
            self.seen_frame_byte = False
        elif b == self.FRAME_BYTE:
            self.seen_frame_byte = True
        else:
            self.current_frame.append(b)

    def read_bytes(self, barr):
        for b in barr:
            self.read_byte(b)
            self.last_byte = b

    def up_to_bytes(self, n):
        collected = 0
        i = 0
        result = bytearray()
        while collected < n and i < len(self.frames):
            collected += len(self.frames[i])
            result = result + self.frames[i]
            i += 1
        if i > 0:
            self.frames = self.frames[i:]
            return result
        else:
            return None

    def bytes_available(self):
        return sum([len(f) for f in self.frames])

    def take(self):
        frames = self.frames
        self.frames = []
        return frames
