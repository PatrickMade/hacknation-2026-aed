"""Minimal QR Code Model 2 encoder: byte mode, error correction level M, versions 1-10.

Written for APP-45 (2026-11-21) because neither portal image ships a QR library.
The algorithm follows ISO/IEC 18004 as described in Project Nayuki's public
"QR Code generator" write-up; this is an independent, reduced implementation.
"""
from xml.sax.saxutils import escape

# Error correction level M: (ECC codewords per block, number of blocks) per version.
_ECC_M = {1: (10, 1), 2: (16, 1), 3: (26, 1), 4: (18, 2), 5: (24, 2),
          6: (16, 4), 7: (18, 4), 8: (22, 4), 9: (22, 5), 10: (26, 5)}
_FORMAT_BITS_M = 0


def _raw_data_modules(ver):
    result = (16 * ver + 128) * ver + 64
    if ver >= 2:
        num_align = ver // 7 + 2
        result -= (25 * num_align - 10) * num_align - 55
        if ver >= 7:
            result -= 36
    return result


def _data_codewords(ver):
    ecc_len, blocks = _ECC_M[ver]
    return _raw_data_modules(ver) // 8 - ecc_len * blocks


def _gf_mul(x, y):
    z = 0
    for i in reversed(range(8)):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z


def _rs_divisor(degree):
    result = [0] * (degree - 1) + [1]
    root = 1
    for _ in range(degree):
        for j in range(degree):
            result[j] = _gf_mul(result[j], root)
            if j + 1 < degree:
                result[j] ^= result[j + 1]
        root = _gf_mul(root, 0x02)
    return result


def _rs_remainder(data, divisor):
    result = [0] * len(divisor)
    for byte in data:
        factor = byte ^ result.pop(0)
        result.append(0)
        for i, coef in enumerate(divisor):
            result[i] ^= _gf_mul(coef, factor)
    return result


def _encode_data(payload, ver):
    bits = []

    def put(value, length):
        bits.extend((value >> i) & 1 for i in reversed(range(length)))

    put(0b0100, 4)
    put(len(payload), 8 if ver <= 9 else 16)
    for byte in payload:
        put(byte, 8)
    capacity = _data_codewords(ver) * 8
    put(0, min(4, capacity - len(bits)))
    put(0, -len(bits) % 8)
    pad = 0xEC
    while len(bits) < capacity:
        put(pad, 8)
        pad ^= 0xEC ^ 0x11
    return [int(''.join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]


def _add_ecc_and_interleave(data, ver):
    ecc_len, num_blocks = _ECC_M[ver]
    raw_codewords = _raw_data_modules(ver) // 8
    num_short = num_blocks - raw_codewords % num_blocks
    short_len = raw_codewords // num_blocks
    divisor = _rs_divisor(ecc_len)
    blocks, k = [], 0
    for i in range(num_blocks):
        size = short_len - ecc_len + (0 if i < num_short else 1)
        block = data[k:k + size]
        k += size
        ecc = _rs_remainder(block, divisor)
        if i < num_short:
            block = block + [None]
        blocks.append(block + ecc)
    result = []
    for i in range(len(blocks[0])):
        for block in blocks:
            if block[i] is not None:
                result.append(block[i])
    return result


class _Matrix:
    def __init__(self, ver):
        self.ver = ver
        self.size = ver * 4 + 17
        self.dark = [[False] * self.size for _ in range(self.size)]
        self.function = [[False] * self.size for _ in range(self.size)]

    def set_function(self, x, y, dark):
        self.dark[y][x] = dark
        self.function[y][x] = True

    def alignment_positions(self):
        if self.ver == 1:
            return []
        num_align = self.ver // 7 + 2
        step = (self.ver * 8 + num_align * 3 + 5) // (num_align * 4 - 4) * 2
        return list(reversed([self.size - 7 - i * step for i in range(num_align - 1)] + [6]))

    def draw_function_patterns(self):
        for i in range(self.size):
            self.set_function(6, i, i % 2 == 0)
            self.set_function(i, 6, i % 2 == 0)
        for cx, cy in ((3, 3), (self.size - 4, 3), (3, self.size - 4)):
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    x, y = cx + dx, cy + dy
                    if 0 <= x < self.size and 0 <= y < self.size:
                        self.set_function(x, y, max(abs(dx), abs(dy)) not in (2, 4))
        positions = self.alignment_positions()
        last = len(positions) - 1
        for i, cx in enumerate(positions):
            for j, cy in enumerate(positions):
                if (i, j) in ((0, 0), (0, last), (last, 0)):
                    continue
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        self.set_function(cx + dx, cy + dy, max(abs(dx), abs(dy)) != 1)
        self.draw_format_bits(0)
        if self.ver >= 7:
            rem = self.ver
            for _ in range(12):
                rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
            bits = self.ver << 12 | rem
            for i in range(18):
                bit = (bits >> i) & 1 == 1
                a, b = self.size - 11 + i % 3, i // 3
                self.set_function(a, b, bit)
                self.set_function(b, a, bit)

    def draw_format_bits(self, mask):
        data = _FORMAT_BITS_M << 3 | mask
        rem = data
        for _ in range(10):
            rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        bits = (data << 10 | rem) ^ 0x5412

        def bit(i):
            return (bits >> i) & 1 == 1

        for i in range(6):
            self.set_function(8, i, bit(i))
        self.set_function(8, 7, bit(6))
        self.set_function(8, 8, bit(7))
        self.set_function(7, 8, bit(8))
        for i in range(9, 15):
            self.set_function(14 - i, 8, bit(i))
        for i in range(8):
            self.set_function(self.size - 1 - i, 8, bit(i))
        for i in range(8, 15):
            self.set_function(8, self.size - 15 + i, bit(i))
        self.set_function(8, self.size - 8, True)

    def draw_codewords(self, codewords):
        i, total = 0, len(codewords) * 8
        right = self.size - 1
        while right >= 1:
            if right == 6:
                right = 5
            for vert in range(self.size):
                for j in range(2):
                    x = right - j
                    upward = ((right + 1) & 2) == 0
                    y = self.size - 1 - vert if upward else vert
                    if not self.function[y][x] and i < total:
                        self.dark[y][x] = (codewords[i >> 3] >> (7 - (i & 7))) & 1 == 1
                        i += 1
            right -= 2

    def apply_mask(self, mask):
        rules = (
            lambda x, y: (x + y) % 2 == 0,
            lambda x, y: y % 2 == 0,
            lambda x, y: x % 3 == 0,
            lambda x, y: (x + y) % 3 == 0,
            lambda x, y: (x // 3 + y // 2) % 2 == 0,
            lambda x, y: x * y % 2 + x * y % 3 == 0,
            lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0,
            lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0,
        )
        rule = rules[mask]
        for y in range(self.size):
            for x in range(self.size):
                if not self.function[y][x] and rule(x, y):
                    self.dark[y][x] = not self.dark[y][x]

    def penalty(self):
        lines = [row for row in self.dark] + [list(col) for col in zip(*self.dark)]
        score = 0
        finder_a = [True, False, True, True, True, False, True, False, False, False, False]
        finder_b = list(reversed(finder_a))
        for line in lines:
            run, prev = 0, None
            for value in line:
                if value == prev:
                    run += 1
                    if run == 5:
                        score += 3
                    elif run > 5:
                        score += 1
                else:
                    run, prev = 1, value
            padded = [False] * 4 + list(line) + [False] * 4
            for k in range(len(padded) - 10):
                window = padded[k:k + 11]
                if window == finder_a or window == finder_b:
                    score += 40
        for y in range(self.size - 1):
            for x in range(self.size - 1):
                v = self.dark[y][x]
                if v == self.dark[y][x + 1] == self.dark[y + 1][x] == self.dark[y + 1][x + 1]:
                    score += 3
        dark = sum(map(sum, self.dark))
        total = self.size * self.size
        score += ((abs(dark * 20 - total * 10) + total - 1) // total - 1) * 10
        return score


def encode(text, mask=None):
    """Return the QR module matrix (list of rows, True = dark) for a UTF-8 string."""
    payload = text.encode('utf-8')
    ver = next((v for v in _ECC_M if 4 + (8 if v <= 9 else 16) + 8 * len(payload) <= _data_codewords(v) * 8), None)
    if ver is None:
        raise ValueError('Text too long for QR versions 1-10 at level M.')
    codewords = _add_ecc_and_interleave(_encode_data(payload, ver), ver)
    best = None
    for candidate in ([mask] if mask is not None else range(8)):
        matrix = _Matrix(ver)
        matrix.draw_function_patterns()
        matrix.draw_codewords(codewords)
        matrix.apply_mask(candidate)
        matrix.draw_format_bits(candidate)
        score = matrix.penalty()
        if best is None or score < best[0]:
            best = (score, matrix)
    return best[1].dark


def svg(text, title, border=4, scale=8):
    """Render text as a standalone, scalable SVG QR code."""
    rows = encode(text)
    size = len(rows) + 2 * border
    path = ''.join(
        'M{},{}h1v1h-1z'.format(x + border, y + border)
        for y, row in enumerate(rows) for x, dark in enumerate(row) if dark
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s} {s}" width="{px}" height="{px}" '
        'role="img" aria-labelledby="qr-title" shape-rendering="crispEdges">'
        '<title id="qr-title">{title}</title>'
        '<rect width="{s}" height="{s}" fill="#fff"/><path fill="#000" d="{path}"/></svg>'
    ).format(s=size, px=size * scale, title=escape(title), path=path)
