import struct
from tpk2 import jdlz as decompress


def compress(data, max_chain=16):
    data = bytes(data)
    n = len(data)
    out = bytearray(b'JDLZ\x02\x10\x00\x00' + struct.pack('<II', n, 0))
    f1_pos = None; f1_bits = 0; f1_cnt = 8
    f2_pos = None; f2_bits = 0; f2_cnt = 8
    table = {}
    i = 0

    def insert(pos):
        if pos + 3 <= n:
            k = data[pos:pos + 3]
            lst = table.get(k)
            if lst is None:
                table[k] = [pos]
            else:
                lst.append(pos)
                if len(lst) > max_chain:
                    del lst[0]

    while i < n:
        # flag reloads happen at the start of every item, f1 first
        if f1_cnt == 8:
            if f1_pos is not None:
                out[f1_pos] = f1_bits
            f1_pos = len(out); out.append(0); f1_bits = 0; f1_cnt = 0
        if f2_cnt == 8:
            if f2_pos is not None:
                out[f2_pos] = f2_bits
            f2_pos = len(out); out.append(0); f2_bits = 0; f2_cnt = 0
        best_len = 0; best_off = 0
        if i + 3 <= n:
            cands = table.get(data[i:i + 3], ())
            for p in reversed(cands):
                off = i - p
                if off > 2064:
                    continue
                maxl = 4098 if off <= 16 else 34
                l = 3
                lim = min(maxl, n - i)
                while l < lim and data[p + l] == data[i + l]:
                    l += 1
                if l > best_len:
                    best_len = l; best_off = off
                    if l == lim:
                        break
            # run-length via short offsets (overlapping copies)
            if best_len < 8:
                for off in (1, 2, 4, 8, 16):
                    if off > i:
                        break
                    l = 0
                    lim = min(4098, n - i)
                    while l < lim and data[i + l - off] == data[i + l]:
                        l += 1
                    if l > best_len and l >= 3:
                        best_len = l; best_off = off
        if best_len >= 3:
            f1_bits |= 1 << f1_cnt
            if best_off <= 16:
                f2_bits |= 1 << f2_cnt
                L = best_len - 3
                out.append(((L >> 4) & 0xF0) | (best_off - 1))
                out.append(L & 0xFF)
            else:
                T = best_off - 17
                out.append(((T >> 3) & 0xE0) | (best_len - 3))
                out.append(T & 0xFF)
            f2_cnt += 1
            for k in range(best_len):
                insert(i + k)
            i += best_len
        else:
            out.append(data[i])
            insert(i)
            i += 1
        f1_cnt += 1
    if f1_pos is not None:
        out[f1_pos] = f1_bits
    if f2_pos is not None:
        out[f2_pos] = f2_bits
    struct.pack_into('<I', out, 12, len(out))
    return bytes(out)


if __name__ == '__main__':
    import os, time
    for t in [b'', b'a', b'abcabcabcabcabcabcabcabcabc' * 50, os.urandom(3000) + b'\0' * 9000 + os.urandom(100)]:
        c = compress(t)
        assert decompress(c) == t, (len(t))
    d = open('mw/CARS/MUSTANGGT/TEXTURES.BIN', 'rb').read()[:600000]
    t0 = time.time(); c = compress(d); print(len(d), len(c), time.time() - t0)
    assert decompress(c) == d
    print('ok')
