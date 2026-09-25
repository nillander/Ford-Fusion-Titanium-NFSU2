"""Convert the MW2005 Fusion GEOMETRY.BIN into an NFSU2 solid list for the FOCUS slot.

Reads Most Wanted chunks (Arushan mwgc, GAME_NFSMW) and writes the Underground 2
layout used by retail CARS/FOCUS/GEOMETRY.BIN. Source files are only read.
"""
import struct
import sys
from pathlib import Path

MW_GROUP = 104
U2_GROUP = 60


def real_hash(name: str) -> int:
    value = 0xFFFFFFFF
    for char in name:
        value = (value * 33 + ord(char)) & 0xFFFFFFFF
    return value


def align(n, boundary):
    return (n + boundary - 1) & ~(boundary - 1)


class Reader:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def u32(self):
        v = struct.unpack_from("<I", self.data, self.pos)[0]
        self.pos += 4
        return v

    def i32(self):
        v = struct.unpack_from("<i", self.data, self.pos)[0]
        self.pos += 4
        return v

    def f32(self):
        v = struct.unpack_from("<f", self.data, self.pos)[0]
        self.pos += 4
        return v

    def bytes(self, n):
        v = self.data[self.pos : self.pos + n]
        self.pos += n
        return v

    def align(self, boundary):
        pad = (-self.pos) & (boundary - 1)
        self.pos += pad

    def cstring(self):
        end = self.data.index(b"\x00", self.pos)
        text = self.data[self.pos : end].decode("latin1")
        self.pos = end + 1
        return text


def parse_mw(path: Path):
    data = path.read_bytes()
    reader = Reader(data)
    parts = []

    def parse_range(end):
        while reader.pos + 8 <= end:
            start = reader.pos
            kind = reader.u32()
            length = reader.u32()
            chunk_end = reader.pos + length
            if kind & 0x80000000:
                parse_range(chunk_end)
            else:
                parse_leaf(kind, chunk_end)
            reader.pos = chunk_end
            if reader.pos < start:
                raise RuntimeError("chunk went backwards")

    def parse_leaf(kind, chunk_end):
        if kind == 0x134011:
            reader.align(0x10)
            info = {
                "pre": reader.bytes(12),
                "unk1": reader.u32(),
                "hash": reader.u32(),
                "tris": reader.i32(),
                "counts": reader.bytes(4),
                "null6": reader.i32(),
                "bound_min": reader.bytes(16),
                "bound_max": reader.bytes(16),
                "transform": reader.bytes(64),
                "null7": reader.i32(),
                "null8": reader.i32(),
                "unk2": reader.i32(),
                "unk3": reader.i32(),
                "null9": reader.i32(),
                "unk4": reader.i32(),
                "unk5": reader.f32(),
                "unk6": reader.f32(),
            }
            info["name"] = reader.cstring()
            parts.append({"info": info, "textures": [], "shaders": [], "mounts": b"", "groups": [], "vertices": b"", "indices": b""})
        elif kind == 0x134012 and parts:
            blob = reader.data[reader.pos : chunk_end]
            parts[-1]["textures"] = [struct.unpack_from("<I", blob, i)[0] for i in range(0, len(blob) - 7, 8)]
        elif kind == 0x134013 and parts:
            blob = reader.data[reader.pos : chunk_end]
            parts[-1]["shaders"] = [struct.unpack_from("<I", blob, i)[0] for i in range(0, len(blob) - 7, 8)]
        elif kind == 0x13401A and parts:
            reader.align(0x10)
            parts[-1]["mounts"] = reader.data[reader.pos : chunk_end]
        elif kind == 0x134900 and parts:
            reader.align(0x10)
            part = parts[-1]
            part["plat"] = {
                "null1": reader.i32(),
                "null2": reader.i32(),
                "unk1": reader.i32(),
                "flags": reader.i32(),
                "groups": reader.i32(),
                "null2_mw": reader.i32(),
                "vb": reader.i32(),
                "nulls": reader.bytes(16),
                "index_count": reader.i32(),
            }
        elif kind == 0x134B02 and parts:
            reader.align(0x10)
            blob = reader.data[reader.pos : chunk_end]
            if len(blob) % MW_GROUP != 0:
                raise RuntimeError(f"shading group size {len(blob)} is not {MW_GROUP}")
            groups = []
            for off in range(0, len(blob), MW_GROUP):
                bmin = blob[off : off + 12]
                bmax = blob[off + 12 : off + 24]
                tex = blob[off + 24]
                shader = blob[off + 29]
                flags, verts, tris, index_off, length = struct.unpack_from("<5I", blob, off + 56)
                groups.append(
                    {
                        "min": bmin,
                        "max": bmax,
                        "tex": tex,
                        "shader": shader,
                        "flags": flags,
                        "verts": verts,
                        "tris": tris,
                        "offset": index_off,
                        "length": length,
                    }
                )
            parts[-1]["groups"] = groups
        elif kind == 0x134B01 and parts:
            reader.align(0x80)
            parts[-1]["vertices"] = reader.data[reader.pos : chunk_end]
        elif kind == 0x134B03 and parts:
            reader.align(0x10)
            parts[-1]["indices"] = reader.data[reader.pos : chunk_end]

    parse_range(len(data))
    if not parts:
        raise RuntimeError("no solids found")
    return parts


def rename_part(name: str) -> str:
    if name.startswith("MUSTANGGT_"):
        return "FOCUS_" + name[len("MUSTANGGT_") :]
    return name


def ug2_vertices(part):
    groups = part["groups"]
    count = sum(g["verts"] for g in groups) or 0
    raw = part["vertices"]
    if count == 0:
        return raw, 0
    if len(raw) % count != 0:
        raise RuntimeError(f"{part['info']['name']} vertex buffer {len(raw)} not divisible by {count}")
    stride = len(raw) // count
    if stride == 36:
        return raw, count
    if stride < 36:
        raise RuntimeError(f"{part['info']['name']} stride {stride}")
    out = bytearray()
    for i in range(count):
        out += raw[i * stride : i * stride + 36]
    return bytes(out), count


def write_ug2(parts, dest: Path):
    renamed = []
    for part in parts:
        info = dict(part["info"])
        info["name"] = rename_part(info["name"])
        info["hash"] = real_hash(info["name"])
        cloned = dict(part)
        cloned["info"] = info
        verts, vcount = ug2_vertices(part)
        indices = part["indices"]
        # Underground 2 stops the game when one solid carries more than 65535 indices.
        if len(indices) > 60000 * 2 and part["groups"]:
            indices = indices[: 60000 * 2]
            group = dict(part["groups"][0])
            group["length"] = 60000
            group["tris"] = 20000
            group["verts"] = vcount
            cloned["groups"] = [group]
            cloned["info"]["tris"] = 20000
        cloned["vertices"] = verts
        cloned["indices"] = indices
        cloned["vcount"] = vcount
        renamed.append(cloned)

    buf = bytearray()

    def begin(kind):
        start = len(buf)
        buf.extend(struct.pack("<II", kind, 0))
        return start

    def end(start):
        length = len(buf) - start - 8
        struct.pack_into("<I", buf, start + 4, length)

    def pad(boundary):
        while len(buf) % boundary:
            start = begin(0)
            missing = (-(len(buf))) & (boundary - 1)
            buf.extend(b"\x00" * missing)
            end(start)

    root = begin(0x80134000)
    begin(0)
    end(begin(0) if False else len(buf) - 8)

    catalog = begin(0x80134001)
    desc = begin(0x134002)
    # Retail Underground 2 header is 144 bytes: 16 unknown, counts, 0x38 path, 0x20 class, tail.
    # Unk1 0x1C is the UG2 value from mwgc (MW uses 0x1D).
    path = b"..\\PC\\CDUG2\\CARS\\FOCUS\\GEOMETRY.BIN".ljust(0x38, b"\x00")
    klass = b"DEFAULT".ljust(0x20, b"\x00")
    # Retail cars use header value 0x1D and a 144-byte descriptor.
    buf.extend(struct.pack("<4I", 0, 0, 0x1D, len(renamed)))
    buf.extend(path)
    buf.extend(klass)
    buf.extend(struct.pack("<10I", 0, 0, 0x80, 0, 0, 0, 0, 0, 0, 0))
    end(desc)

    hashes = begin(0x134003)
    order = sorted(range(len(renamed)), key=lambda i: renamed[i]["info"]["hash"])
    for index in order:
        buf.extend(struct.pack("<II", renamed[index]["info"]["hash"], 0))
    end(hashes)

    offs = begin(0x134004)
    off_at = len(buf)
    buf.extend(b"\x00" * (len(renamed) * 24))
    end(offs)

    empty = begin(0x80134008)
    end(empty)
    end(catalog)

    part_chunks = []
    for part in renamed:
        pad(0x80)
        part_at = begin(0x80134010)
        info = part["info"]
        head = begin(0x134011)
        while len(buf) % 16:
            buf.append(0)
        buf.extend(info["pre"])
        buf.extend(struct.pack("<III", 0x400016, info["hash"], info["tris"] & 0xFFFFFFFF))
        buf.extend(info["counts"])
        buf.extend(struct.pack("<i", info["null6"]))
        buf.extend(info["bound_min"])
        buf.extend(info["bound_max"])
        buf.extend(info["transform"])
        buf.extend(struct.pack("<5i", 0x3F800000, 0, 0xEE580, 0xEE580, 0))
        buf.extend(struct.pack("<ffii", info["unk5"], info["unk6"], 0, 0))
        raw_name = info["name"].encode("latin1")[:27]
        buf.extend(raw_name.ljust(0x1C, b"\x00"))
        end(head)

        tex = begin(0x134012)
        for value in part["textures"]:
            buf.extend(struct.pack("<II", value, 0))
        end(tex)
        sh = begin(0x134013)
        for value in part["shaders"]:
            buf.extend(struct.pack("<II", value, 0))
        end(sh)
        if part["mounts"]:
            mounts = begin(0x13401A)
            while len(buf) % 16:
                buf.append(0)
            buf.extend(part["mounts"])
            end(mounts)

        data = begin(0x80134100)
        groups = part["groups"]
        index_count = len(part["indices"]) // 2
        plat = begin(0x134900)
        while len(buf) % 16:
            buf.append(0)
        desc_at = len(buf)
        flags = part.get("plat", {}).get("flags", 0x4000) | 0x80
        buf.extend(struct.pack("<5i", 0, 0, 0x10, flags, len(groups)))
        buf.extend(b"\x00" * 16)
        buf.extend(struct.pack("<4i", index_count // 3, 0, 0, 0))
        buf.extend(struct.pack("<4i", part["vcount"], 0, 0, 0))
        end(plat)

        verts = begin(0x134B01)
        while len(buf) % 0x80:
            buf.append(0)
        buf.extend(part["vertices"])
        end(verts)

        grp = begin(0x134B02)
        while len(buf) % 16:
            buf.append(0)
        # The game asserts when one shading group has more than 65535 indices.
        cursor = 0
        written_groups = 0
        for group in groups:
            length = group["length"] or group["tris"] * 3
            piece = 0
            while piece < length:
                take = min(60000, length - piece)
                buf.extend(group["min"])
                buf.extend(struct.pack("<I", take))
                buf.extend(group["max"])
                buf.extend(struct.pack("<6I", group["tex"], group["shader"], 0, 0, 0, 0))
                buf.extend(struct.pack("<II", cursor + piece, group["flags"] | 0x100))
                piece += take
                written_groups += 1
            cursor += length
        end(grp)
        # Patch the group count in the plat descriptor now that groups may have been split.
        # Descriptor layout: 5 ints, 16 zero bytes, NumTris, three zeros, NumVerts, three zeros.
        struct.pack_into("<i", buf, desc_at + 16, written_groups)

        idx = begin(0x134B03)
        while len(buf) % 16:
            buf.append(0)
        buf.extend(part["indices"])
        if len(part["indices"]) % 2:
            buf.append(0)
        end(idx)
        end(data)
        end(part_at)
        part_chunks.append(part_at)

    end(root)
    while len(buf) % 0x80:
        buf.append(0)

    # Fill the hash-sorted offset table: hash, offset, size, size, 0, 0.
    for position, index in enumerate(order):
        at = off_at + position * 24
        start = part_chunks[index]
        size = struct.unpack_from("<I", buf, start + 4)[0] + 8
        struct.pack_into("<IIIIII", buf, at, renamed[index]["info"]["hash"], start, size, size, 0, 0)

    dest.write_bytes(buf)
    return renamed


def main():
    source = Path(sys.argv[1])
    dest = Path(sys.argv[2])
    parts = parse_mw(source)
    written = write_ug2(parts, dest)
    body = next(p for p in written if p["info"]["name"] == "FOCUS_KIT00_BODY_A")
    bmin = struct.unpack("<4f", body["info"]["bound_min"])
    bmax = struct.unpack("<4f", body["info"]["bound_max"])
    print(f"parts={len(written)} bytes={dest.stat().st_size}")
    print(f"body_x={bmin[0]:.3f}..{bmax[0]:.3f} y={bmin[1]:.3f}..{bmax[1]:.3f} z={bmin[2]:.3f}..{bmax[2]:.3f}")
    print(f"hash FOCUS_KIT00_BODY_A={real_hash('FOCUS_KIT00_BODY_A'):08X}")


if __name__ == "__main__":
    main()
