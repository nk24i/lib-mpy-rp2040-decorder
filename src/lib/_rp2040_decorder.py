from machine import Pin
import rp2
from struct import unpack
import utime


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


class Preamble:
    def __init__(self):
        self.reset()

    def __call__(self, pulse):
        if pulse == 1:
            if self.preamble < 14:
                self.preamble += 1
        else:
            if self.preamble < 14:
                # ERROR
                self.reset()
            else:
                self.is_got_preamble = True
        return self.is_got_preamble

    def reset(self):
        self.preamble = 0
        self.is_got_preamble = False


class Captcha:
    def __init__(self):
        self.clear()

    def __call__(self, pulse):
        if self.count and self.count % 8 == 0:
            # print('separator', pulse, self.packets)
            if pulse == 1:  # packet end bit
                error = self.detect_error()
                if not error:
                    return self.packets
                else:
                    # raise InvalidPacketError  # TODO: create error class
                    pass
            else:  # next packet start bit
                pass  # TODO:ビット列の長さでバリデーション
        else:
            if self.packets is None:
                self.packets = pulse
            else:
                self.packets <<= 1
                self.packets |= pulse
        self.count += 1

    def clear(self):
        self.packets = None
        self.count = 0

    def validate(self):
        # print(self.packets)
        return True  # TODO: Impl.

    def detect_error(self):
        # print(bin(self.packets))
        # print("\n")
        return False
        # packet_array = unpack("B" * len(self.packets), self.packets)
        # xor_packets = reduce(lambda i, j: i ^ j, packet_array[0:-1])
        # check_packet = packet_array[-1]
        # return not xor_packets == check_packet


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
        self.on_captcha = False  # if False waiting got valid preamble
        self.preamble = Preamble()
        self.captcha = Captcha()

    def iter_event(self):
        while True:
            counts = self.sm.get().to_bytes(4, "little")  # 20us 程度
            count_array = unpack("<BBBB", counts)
            for count in count_array:
                yield count

    def count_to_captcha(self, count):
        signal_level = 1 if count > 13 and count < 16 else 0
        if self.on_captcha:
            packet = self.captcha(signal_level)
            if packet is not None:
                self.on_captcha = False
                self.captcha.clear()
                print(bin(packet), packet)
                # TODO: packet to command
        else:
            is_got_preamble = self.preamble(signal_level)
            if is_got_preamble:
                self.on_captcha = True
                self.preamble.reset()

    def run(self):
        self.sm.active(1)
        for count in self.iter_event():
            self.count_to_captcha(count)


receiver = Receiver(0, 3)
receiver.run()
