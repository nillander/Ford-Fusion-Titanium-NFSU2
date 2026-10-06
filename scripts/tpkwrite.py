"""Writes an NFS Underground 2 car TEXTURES.BIN in the nfsu360 compiler layout (JDLZ blobs)."""
import struct
import jdlz

INFO_PATH = b'NFS:U2/MW Texture Compiler by nfsu360'


def build_info(template, name, h, w, hgt, data_size, placement):
    ti = bytearray(template)
    nm = name.encode('latin1')[:23]
    ti[12:36] = nm.ljust(24, b'\0')
    struct.pack_into('<I', ti, 36, h)
    struct.pack_into('<I', ti, 44, 0)
    struct.pack_into('<I', ti, 48, placement)
    struct.pack_into('<I', ti, 52, placement + data_size)
    struct.pack_into('<I', ti, 56, data_size)
    struct.pack_into('<I', ti, 60, 0)
    struct.pack_into('<I', ti, 64, data_size)
    struct.pack_into('<HH', ti, 68, w, hgt)
    ti[72] = (w - 1).bit_length(); ti[73] = (hgt - 1).bit_length()
    ti[78] = 1
    return bytes(ti)


def write(textures, path):
    """textures: list of dict(hash, info(124), dds(32), data, tail=b'')"""
    textures = sorted(textures, key=lambda t: t['hash'])
    place = 0
    for t in textures:  # ImagePlacement is cumulative in hash order (as the nfsu360 compiler writes it)
        ti = bytearray(t['info'])
        size = struct.unpack_from('<I', ti, 56)[0]
        struct.pack_into('<II', ti, 48, place, place + size)
        place += size
        t['info'] = bytes(ti)
    blobs = []
    for t in textures:
        raw = t['data'] + t.get('tail', b'') + t['info'] + t['dds']
        blobs.append((jdlz.compress(raw), len(raw)))
    out = bytearray()
    out += struct.pack('<II', 0xB3300000, 0)
    out += struct.pack('<II', 0, 48) + b'\0' * 48
    hdr_at = len(out)
    out += struct.pack('<II', 0xB3310000, 0)
    info = bytearray(124)
    struct.pack_into('<I', info, 0, 5)
    info[32:96] = INFO_PATH.ljust(64, b'\0')
    out += struct.pack('<II', 0x33310001, 124) + info
    out += struct.pack('<II', 0x33310002, 8 * len(textures))
    for t in textures:
        out += struct.pack('<II', t['hash'], 0)
    out += struct.pack('<II', 0x33310003, 24 * len(textures))
    dos_at = len(out)
    out += b'\0' * (24 * len(textures))
    struct.pack_into('<I', out, hdr_at + 4, len(out) - hdr_at - 8)
    need = (-(len(out) + 8)) % 0x80
    out += struct.pack('<II', 0, need) + b'\0' * need
    for i, (t, (blob, rawlen)) in enumerate(zip(textures, blobs)):
        struct.pack_into('<6I', out, dos_at + 24 * i, t['hash'], len(out), len(blob), rawlen, 0x100, 0)
        out += blob
    struct.pack_into('<I', out, 4, len(out) - 8)
    open(path, 'wb').write(out)
    return len(out)


def write_raw(textures, path, template=None):
    """Uncompressed (RAWW) TPK in the mwtc layout.  The old Cursor port used the MW TPK as-is in
    this slot and the game loaded it, so this layout is known to be accepted by UG2.
    The two header chunks (0x33310001, 0x33320001) are copied from the template; they are the same bytes
    in both MW releases and in the installed v9, so any of them works (default: ports.TEMPLATE)."""
    import ug2, ports
    tm = open(template or ports.TEMPLATE, 'rb').read()
    info = c1 = None
    for a, b, p, s in ug2.chunks(tm, 0, len(tm), 0, []):
        if b == 0x33310001: info = tm[p + 8:p + 8 + s]
        if b == 0x33320001: c1 = tm[p + 8:p + 8 + s]
    textures = sorted(textures, key=lambda t: t['hash'])
    place = 0
    for t in textures:
        ti = bytearray(t['info'])
        size = struct.unpack_from('<I', ti, 56)[0]
        struct.pack_into('<II', ti, 48, place, place + size)
        place += size
        t['info'] = bytes(ti)
    out = bytearray()
    out += struct.pack('<II', 0xB3300000, 0)
    out += struct.pack('<II', 0, 48) + b'\0' * 48
    hdr_at = len(out)
    out += struct.pack('<II', 0xB3310000, 0)
    out += struct.pack('<II', 0x33310001, len(info)) + info
    out += struct.pack('<II', 0x33310002, 8 * len(textures))
    for t in textures:
        out += struct.pack('<II', t['hash'], 0)
    out += struct.pack('<II', 0x33310003, 24 * len(textures))
    dos_at = len(out)
    out += b'\0' * (24 * len(textures))
    struct.pack_into('<I', out, hdr_at + 4, len(out) - hdr_at - 8)
    need = (-(len(out) + 8)) % 0x80
    out += struct.pack('<II', 0, need) + b'\0' * need
    data_root = len(out)
    out += struct.pack('<II', 0xB3320000, 0)
    out += struct.pack('<II', 0x33320001, len(c1)) + c1
    need = (-(len(out) + 8)) % 0x80
    out += struct.pack('<II', 0, need) + b'\0' * need
    d2 = len(out)
    out += struct.pack('<II', 0x33320002, 0)
    while len(out) % 0x80:
        out.append(0)
    for i, t in enumerate(textures):
        while len(out) % 0x80:
            out.append(0)
        raw = t['data'] + t.get('tail', b'') + t['info'] + t['dds']
        blob = b'RAWW\x01\x10\x00\x00' + struct.pack('<II', len(raw), len(raw) + 16) + raw
        struct.pack_into('<6I', out, dos_at + 24 * i, t['hash'], len(out), len(blob), len(raw), 0x100, 0)
        out += blob
    while len(out) % 0x80:
        out.append(0)
    struct.pack_into('<I', out, d2 + 4, len(out) - d2 - 8)
    struct.pack_into('<I', out, data_root + 4, len(out) - data_root - 8)
    struct.pack_into('<I', out, 4, len(out) - 8)
    open(path, 'wb').write(out)
    return len(out)
