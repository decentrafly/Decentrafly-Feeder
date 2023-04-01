import unittest
import beast

class TestBeastDecoder(unittest.TestCase):

    def test_decode_frame_after_prefix(self):
        d = beast.Decoder()
        d.read_bytes([0, 26, 49, 1, 1, 1, 26, 49, 0])
        self.assertEqual(len(d.frames), 1)
        self.assertEqual(d.frames[0], bytearray([26, 49, 1, 1, 1]))

    def test_frames_can_be_split(self):
        d = beast.Decoder()
        d.read_bytes([0, 26, 49, 1, 1, 1, 26, 49, 0])
        d.read_bytes([1, 26, 50])
        self.assertEqual(len(d.frames), 2)
        self.assertEqual(d.frames[0], bytearray([26, 49, 1, 1, 1]))
        self.assertEqual(d.frames[1], bytearray([26, 49, 0, 1]))

if __name__ == '__main__':
    unittest.main()
