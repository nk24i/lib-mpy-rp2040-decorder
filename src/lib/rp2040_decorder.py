from functools import reduce
from struct import unpack


class Captcha():
    def __init__(self):
        self.packets = b""

    def detect_error(self):
        packet_array = unpack("B" * len(self.packets), self.packets)
        xor_packets = reduce(lambda i, j: i ^ j, packet_array[0:-1])
        check_packet = packet_array[-1]
        return not xor_packets == check_packet
        # TODO: add tests