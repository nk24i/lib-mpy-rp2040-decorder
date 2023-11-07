from functools import reduce
from machine import Pin
import rp2
from struct import unpack


@rp2.asm_pio(
    set_init=rp2.PIO.IN_LOW,
    fifo_join=rp2.PIO.JOIN_RX,
    in_shiftdir=rp2.PIO.SHIFT_RIGHT,
    autopush=True,
)
def decode_dcc_pulse():
    set(pindirs, 0)
    wrap_target()
    set(x, 31)
    wait(0, pin, 0)
    label("dec_count")
    jmp(pin, "write")
    jmp(x_dec, "dec_count")
    label("write")
    in_(x, 8)
    wrap()


class Captcha:
    def __init__(self):
        self.packets = b""

    def detect_error(self):
        packet_array = unpack("B" * len(self.packets), self.packets)
        xor_packets = reduce(lambda i, j: i ^ j, packet_array[0:-1])
        check_packet = packet_array[-1]
        return not xor_packets == check_packet


class Receiver:
    def __init__(self, pin_id, address):
        pin_obj = Pin(pin_id)
        self.sm = rp2.StateMachine(
            pin_id,
            decode_dcc_pulse,
            freq=500000,  # 2us/count
            in_base=pin_obj,
            jmp_pin=pin_obj,
            set_base=pin_obj,
            push_thresh=256,  # 32bit(8bit*4, per FIFO)*8 -> 32pulse
        )

    def run(self):
        self.sm.active(1)
