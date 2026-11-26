"""Host-only MMIO and two-copy cache model. The mock returns scripted words."""

import unittest
from unittest.mock import patch

import host


class Buffer:
    def __init__(self, depth, dtype, address):
        self.device_address = address
        self.nbytes = depth * {"int16": 2, "int32": 4}[dtype]
        self.host = [None] * depth
        self.ddr = None
        self.freed = False

    def __setitem__(self, key, value):
        self.host[key] = value

    def __iter__(self):
        return iter(self.host)

    def flush(self):
        self.ddr = self.host.copy()

    def invalidate(self):
        self.host = self.ddr.copy()

    def freebuffer(self):
        self.freed = True


class MockBoard:
    """Simulate control and storage only. No kernel recurrence runs here."""

    def __init__(self):
        self.registers = {name: {"address_offset": offset, "size": size}
                          for name, offset, size in (
                              ("CTRL", 0, 32), ("signal_r_1", 16, 32), ("signal_r_2", 20, 32),
                              ("reference", 32, 64), ("result", 48, 64),
                              ("signal_size", 64, 32), ("reference_size", 72, 32), ("width", 80, 32))}
        self.flags = 6  # Simulate a previous AP_DONE and AP_IDLE.
        self.mmio = {}
        self.buffers = []
        self.base = 1 << 32
        self.scripted = (0, 2, 1, 2)
        self.received = None

    def allocate(self, shape, dtype):
        buffer = Buffer(shape[0], dtype, self.base + 4096 * len(self.buffers))
        self.buffers.append(buffer)
        return buffer

    def read(self, offset):
        assert offset == 0
        flags = self.flags
        self.flags &= ~2
        return flags

    def write(self, offset, value):
        if offset:
            self.mmio[offset] = value
            return
        assert value == 1 and self.flags == 4
        by_address = {b.device_address: b for b in self.buffers}
        def resolve(offset):
            high = self.mmio.get(offset + 4, 0)
            return by_address[(high << 32) | self.mmio[offset]]
        signal, reference, result = (resolve(off) for off in (16, 32, 48))
        self.received = (signal.ddr[:self.mmio[64]], reference.ddr[:self.mmio[72]], self.mmio[80])
        assert result.ddr == [-2] * 4
        self.flags = 0
        if self.scripted is not None:
            result.ddr = list(self.scripted)
            self.flags = 6

    def bind(self):
        return host.KernelHost(self, self.registers, self.allocate)


class HostTests(unittest.TestCase):
    def setUp(self):
        self.board = MockBoard()

    def test_signed_codes_high_addresses_and_exact_words(self):
        kernel = self.board.bind()
        self.assertEqual(kernel.compare([40, -5, 12, 30, 45], [-4, 13], 0), (0, 2, 1, 2))
        self.assertEqual(self.board.received, ([40, -5, 12, 30, 45], [-4, 13], 0))
        self.assertTrue(all(b.freed for b in self.board.buffers))
        self.board.scripted = (2, -1, -1, -1)
        self.assertEqual(kernel.compare([7], [7, 7], 0), self.board.scripted)

    def test_all_four_words_are_checked(self):
        kernel = self.board.bind()
        for index in range(4):
            with self.subTest(index=index):
                wrong = [0, 0, 0, 0]
                wrong[index] += 1
                self.board.scripted = wrong
                with self.assertRaisesRegex(AssertionError, "observed"):
                    kernel.compare([1], [1], 0)
                self.assertTrue(all(b.freed for b in self.board.buffers))

    def test_32bit_address_and_end_of_buffer_overflow(self):
        self.board.registers["signal"] = {"address_offset": 16, "size": 32}
        del self.board.registers["signal_r_1"], self.board.registers["signal_r_2"]
        self.board.base = 4096
        kernel = self.board.bind()
        self.board.scripted = (0, 0, 0, 0)
        self.assertEqual(kernel.compare([1], [1], 0), self.board.scripted)
        self.board.base = (1 << 32) - 16 - 4096 * len(self.board.buffers)
        with self.assertRaises(OverflowError):
            kernel.compare([1], [1], 0)
        self.assertTrue(all(b.freed for b in self.board.buffers))

    def test_timeout_pins_buffers_and_blocks_retry(self):
        self.board.scripted = None
        kernel = self.board.bind()
        with patch.object(host, "_pending", []):
            with self.assertRaises(TimeoutError):
                kernel.compare([1], [1], 0, timeout=0.001)
            self.assertEqual(len(host._pending), 3)
            with self.assertRaisesRegex(RuntimeError, "Reboot"):
                kernel.compare([1], [1], 0)
            self.assertFalse(any(b.freed for b in self.board.buffers))

    def test_reject_busy_or_auto_restart(self):
        kernel = self.board.bind()
        for flags in (0, 5, 0x84):
            self.board.flags = flags
            with self.assertRaisesRegex(RuntimeError, "busy"):
                kernel.compare([1], [1], 0)
        self.assertFalse(self.board.buffers)

    def test_bad_inputs_fail_before_allocation(self):
        kernel = self.board.bind()
        for signal, reference, width in (([], [0], 1), ([32768], [0], 0), ([0], [0], 17),
                                         ([1.2], [1], 0), ([1] * 513, [1], 0), ([1], [1] * 129, 0)):
            with self.assertRaises((TypeError, ValueError)):
                kernel.compare(signal, reference, width)
        self.assertFalse(self.board.buffers)

    def test_incomplete_map_fails_at_bind(self):
        del self.board.registers["signal_r_2"]
        with self.assertRaisesRegex(ValueError, "signal"):
            self.board.bind()


if __name__ == "__main__":
    unittest.main()
