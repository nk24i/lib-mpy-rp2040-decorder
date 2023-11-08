from machine import Pin
import rp2
from struct import unpack


@rp2.asm_pio(
    set_init=rp2.PIO.IN_LOW,
    fifo_join=rp2.PIO.JOIN_RX,
    in_shiftdir=rp2.PIO.SHIFT_RIGHT,
    autopush=True,
)
def measure_pulse_length():
    # Measure pulse length by RP2040 programmable I/O
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


class Receiver:
    def __init__(self, pin_id, address):
        pin_obj = Pin(pin_id)
        self.sm = rp2.StateMachine(
            pin_id,
            measure_pulse_length,
            freq=500000,  # 2us/count
            in_base=pin_obj,
            jmp_pin=pin_obj,
            set_base=pin_obj,
            push_thresh=256,  # 32bit(8bit*4, per FIFO)*8 -> 32pulse
        )

    def iter_event(self):
        # Yields pulse length
        while True:
            counts = self.sm.get().to_bytes(4, "little")  # 20us 程度
            count_array = unpack("<BBBB", counts)
            # print(counts, count_array)
            for count in count_array:
                yield count

    def run(self):
        self.sm.active(1)
        for count in self.iter_event():
            print(count)


if __name__ == "__main__":
    receiver = Receiver(0, 3)
    receiver.run()