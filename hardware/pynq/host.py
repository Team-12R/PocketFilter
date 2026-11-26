"""PYNQ transaction for the integer waveform kernel. Run from a repo checkout."""

import math
import operator
import threading
import time
from pathlib import Path

from software.golden_model import MAX_REFERENCE, MAX_SIGNAL, MAX_WIDTH, match


IP_NAME = "sdtw_kernel_0"
# Retain DMA buffers even if a notebook cell drops its host after a timeout.
_pending = []
_lock = threading.Lock()


def _samples(values, limit, name):
    codes = tuple(operator.index(value) for value in values)
    if not 1 <= len(codes) <= limit or any(v < -32768 or v > 32767 for v in codes):
        raise ValueError(f"{name} needs 1..{limit} signed int16 samples")
    return codes


def _register_words(registers, name, pointer=False):
    """Resolve HLS register names, including split pointer words and VHDL suffixes."""
    bases = (name, name + "_r")
    for base in bases:
        if base in registers:
            size = registers[base]["size"]
            offset = registers[base]["address_offset"]
            if size == 64 and pointer:
                return (offset, offset + 4)
            if size == 32:
                if pointer and base + "_1" in registers:
                    second = registers[base + "_1"]
                    if second["size"] == 32 and second["address_offset"] == offset + 4:
                        return (offset, offset + 4)
                    break
                return (offset,)
        elif pointer and base + "_1" in registers and base + "_2" in registers:
            low, high = registers[base + "_1"], registers[base + "_2"]
            if low["size"] == high["size"] == 32 and high["address_offset"] == low["address_offset"] + 4:
                return (low["address_offset"], high["address_offset"])
    raise ValueError(f"Unsupported HWH register {name!r}. Available: {sorted(registers)}")


class KernelHost:
    def __init__(self, ip, registers, allocate):
        self.ip = ip
        self.allocate = allocate
        regs = {name.lower(): entry for name, entry in registers.items()}
        ctrl_name = "ctrl" if "ctrl" in regs else "ap_ctrl"
        self.control, = _register_words(regs, ctrl_name)
        self.pointers = {p: _register_words(regs, p, pointer=True)
                         for p in ("signal", "reference", "result")}
        self.scalars = {p: _register_words(regs, p)[0]
                        for p in ("signal_size", "reference_size", "width")}

    def compare(self, signal, reference, width, timeout=5.0):
        """Return all four signed result words after exact comparison to Python."""
        signal = _samples(signal, MAX_SIGNAL, "signal")
        reference = _samples(reference, MAX_REFERENCE, "reference")
        width = operator.index(width)
        if not 0 <= width <= MAX_WIDTH:
            raise ValueError(f"width must be between 0 and {MAX_WIDTH}")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        best = match(signal, reference, width)
        expected = (0, best.distance, best.start, best.end) if best else (2, -1, -1, -1)
        with _lock:
            if _pending:
                raise RuntimeError("Previous transaction may still access DDR. Reboot the board.")
            flags = self.ip.read(self.control)  # also acknowledges a stale clear-on-read AP_DONE
            if flags & 0x81 or not flags & 0x04:  # AP_START, AUTO_RESTART or !AP_IDLE
                raise RuntimeError(f"Kernel is busy or auto-restarting (control={flags:#x})")
            buffers = []
            try:
                for name, depth, dtype, data in (
                    ("signal", MAX_SIGNAL, "int16", signal),
                    ("reference", MAX_REFERENCE, "int16", reference),
                    ("result", 4, "int32", (-2,) * 4),
                ):
                    buffer = self.allocate(shape=(depth,), dtype=dtype)
                    buffers.append(buffer)
                    buffer[:len(data)] = data
                    buffer.flush()
                    address = int(buffer.device_address)
                    offsets = self.pointers[name]
                    if address < 0 or address + buffer.nbytes > 1 << (32 * len(offsets)):
                        raise OverflowError(f"{name} buffer exceeds the IP address width")
                    for word, offset in enumerate(offsets):
                        self.ip.write(offset, (address >> (32 * word)) & 0xffffffff)
                for name, value in (("signal_size", len(signal)), ("reference_size", len(reference)),
                                    ("width", width)):
                    self.ip.write(self.scalars[name], value)
                deadline = time.monotonic() + timeout
                _pending.extend(buffers)
                self.ip.write(self.control, 1)
                while not self.ip.read(self.control) & 2:  # AP_DONE
                    if time.monotonic() >= deadline:
                        raise TimeoutError("Kernel completion timed out. Reboot the board before retrying.")
                    time.sleep(0.001)
                _pending.clear()
                buffers[-1].invalidate()
                actual = tuple(int(value) for value in buffers[-1])
            finally:
                if not _pending:
                    for buffer in buffers:
                        buffer.freebuffer()
        if actual != expected:
            raise AssertionError(f"(status, distance, start, end): expected {expected}, observed {actual}")
        return actual


def load_overlay(bitfile):
    """Program a paired bitfile and HWH, then bind the generated IP register map."""
    from pynq import Overlay, allocate

    bitfile = Path(bitfile).resolve()
    if bitfile.suffix != ".bit":
        raise ValueError("Pass the .bit path for the overlay")
    for artifact in (bitfile, bitfile.with_suffix(".hwh")):
        if not artifact.is_file():
            raise FileNotFoundError(artifact)
    with _lock:
        if _pending:
            raise RuntimeError("Previous transaction may still access DDR. Reboot the board.")
        overlay = Overlay(str(bitfile), download=False)
        if IP_NAME not in overlay.ip_dict:
            raise ValueError(f"HWH lacks {IP_NAME}. Available: {sorted(overlay.ip_dict)}")
        overlay.download()
        host = KernelHost(getattr(overlay, IP_NAME), overlay.ip_dict[IP_NAME]["registers"], allocate)
    return overlay, host
