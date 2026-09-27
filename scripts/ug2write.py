"""Writes an NFS Underground 2 car GEOMETRY.BIN in the same layout the nfsu360 compiler uses
(validated by rewriting the Escort RS, the donor that loads in the FOCUS slot)."""
import struct
import numpy as np
from hashes import bh

MAX_INDICES = 65535


class Buf:
    def __init__(self):
        self.b = bytearray()

    def begin(self, cid):
        at = len(self.b)
        self.b += struct.pack('<II', cid, 0)
        return at

    def end(self, at):
        struct.pack_into('<I', self.b, at + 4, len(self.b) - at - 8)

    def align(self, a):
        while len(self.b) % a:
            self.b.append(0)

    def pad_chunk(self, a):
        """0x0 chunk so that the next chunk header starts on an `a` boundary (compiler style)."""
        need = (-(len(self.b) + 8)) % a
        self.b += struct.pack('<II', 0, need)
        self.b += b'\0' * need


def vertex_bytes(pos, nrm, col, uv):
    n = len(pos)
    v = np.zeros(n, dtype=[('p', '<f4', 3), ('n', '<f4', 3), ('c', '<u4'), ('t', '<f4', 2)])
    v['p'] = pos; v['n'] = nrm; v['c'] = col; v['t'] = uv
    return v.tobytes()


def marker_bytes(markers):
    out = bytearray()
    for h, m in markers:
        out += struct.pack('<4I', h, 0, 0, 0)
        out += np.asarray(m, '<f4').reshape(16).tobytes()
    return bytes(out)


def write(solids, path, filename_field=b'NFS:U2 Geometry Compiler by nfsu360'):
    # the nfsu360 compiler (and every mod that loads) stores the solids sorted by name hash,
    # in the same order as the 0x134004 offset table
    solids = sorted(solids, key=lambda s: bh(s['name']))
    B = Buf()
    root = B.begin(0x80134000)
    z = B.begin(0); B.end(z)                       # empty 0x0 chunk, as in the compiler output
    cat = B.begin(0x80134001)
    c2 = B.begin(0x134002)
    hdr = bytearray(144)
    struct.pack_into('<II', hdr, 8, 0x1D, len(solids))
    hdr[16:16 + 0x38] = filename_field.ljust(0x38, b'\0')[:0x38]
    hdr[72:72 + 0x20] = b'DEFAULT'.ljust(0x20, b'\0')
    struct.pack_into('<I', hdr, 112, 0x80)
    B.b += hdr
    B.end(c2)
    hashes = [bh(s['name']) for s in solids]
    order = sorted(range(len(solids)), key=lambda i: hashes[i])
    c3 = B.begin(0x134003)
    for i in order:
        B.b += struct.pack('<II', hashes[i], 0)
    B.end(c3)
    c4 = B.begin(0x134004)
    table_at = len(B.b)
    B.b += b'\0' * (24 * len(solids))
    B.end(c4)
    c8 = B.begin(0x80134008); B.end(c8)
    B.end(cat)
    starts = [None] * len(solids)
    for si, s in enumerate(solids):
        B.pad_chunk(0x80)
        start = B.begin(0x80134010)
        starts[si] = start
        # --- header
        nidx = sum(len(g['tri']) * 3 for g in s['groups'])
        ntri = nidx // 3
        assert nidx <= MAX_INDICES, (s['name'], nidx)
        nverts = len(s['pos'])
        assert nverts <= 65535, (s['name'], nverts)
        h = B.begin(0x134011)
        B.align(16)
        B.b += b'\0' * 12
        B.b += struct.pack('<BBH', 0x16, 0, 0x40)
        B.b += struct.pack('<IHH', hashes[si], ntri, 0)
        B.b += struct.pack('<BBBB', 0, len(s['tex']), len(s['light']), 0)
        B.b += b'\0' * 4
        bmin = np.asarray(s['pos']).min(0); bmax = np.asarray(s['pos']).max(0)
        B.b += struct.pack('<3fI', *bmin, 0)
        B.b += struct.pack('<3fI', *bmax, 0)
        B.b += np.eye(4, dtype='<f4').tobytes()
        B.b += struct.pack('<II', 0, 0)
        B.b += struct.pack('<IIIf', 0xEE580, 0xEE580, 0, float(np.linalg.norm(bmax - bmin) / 2))
        B.b += struct.pack('<fII', float(ntri), 0, 0)
        B.b += (s['name'].encode('latin1')[:27] + b'\0').ljust(28, b'\0')
        B.end(h)
        t = B.begin(0x134012)
        for x in s['tex']:
            B.b += struct.pack('<II', x, 0)
        B.end(t)
        t = B.begin(0x134013)
        for x in s['light']:
            B.b += struct.pack('<II', x, 0)
        B.end(t)
        if s.get('markers'):
            t = B.begin(0x13401A)
            B.align(16)
            B.b += marker_bytes(s['markers'])
            B.end(t)
        data = B.begin(0x80134100)
        d = B.begin(0x134900)
        B.align(16)
        B.b += struct.pack('<II', 0, 0)
        B.b += struct.pack('<III', 0x10, 0x4180, len(s['groups']))
        B.b += b'\0' * 16
        B.b += struct.pack('<I', ntri) + b'\0' * 12
        B.b += struct.pack('<I', nverts) + b'\0' * 12
        B.end(d)
        v = B.begin(0x134B01)
        B.align(0x80)
        B.b += vertex_bytes(s['pos'], s['nrm'], s['col'], s['uv'])
        B.end(v)
        g = B.begin(0x134B02)
        B.align(16)
        off = 0
        for gr in s['groups']:
            ln = len(gr['tri']) * 3
            tp = np.asarray(s['pos'])[np.asarray(gr['tri']).reshape(-1)]      # real group bounds (as retail)
            gmn = tp.min(0); gmx = tp.max(0)
            B.b += struct.pack('<3fI3f', *gmn, ln, *gmx)
            B.b += struct.pack('<8I', gr['tex_i'], gr['sh_i'], 0, 0, 0, 0, off, 0x4180)
            off += ln
        B.end(g)
        ib = B.begin(0x134B03)
        B.align(16)
        for gr in s['groups']:
            tri = np.asarray(gr['tri'])
            assert tri.max() < nverts
            B.b += tri.astype('<u2').tobytes()
        B.end(ib)
        B.end(data)
        B.end(start)
    B.pad_chunk(0x80)
    B.end(root)
    for pos_i, i in enumerate(order):
        start = starts[i]
        size = struct.unpack_from('<I', B.b, start + 4)[0] + 8
        struct.pack_into('<6I', B.b, table_at + pos_i * 24, hashes[i], start, size, size, 0, 0)
    open(path, 'wb').write(B.b)
    return len(B.b)
