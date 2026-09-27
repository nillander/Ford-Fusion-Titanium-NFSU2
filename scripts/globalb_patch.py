"""Patches one CarTypeInfo record (chunk 0x34600, 2192-byte records) in GlobalB.lzc.

Usage: python globalb_patch.py <src> <dst> [2018|2012]
Both ports share the 2018 chassis: Corolla torque scaled to 248 cv, Lancer tyres and
suspension, mass 1.63 t, Fusion wheelbase.  2018 writes the MUSTANG record with torque
split 0.5 (AWD).  2012 writes the FOCUS record with torque split 1.0 (FWD).
Wheel Z, tyre radius and width stay as they are in the input file.
"""
import math, struct, sys, json
import ug2
import ports

REC = 2192
src, dst = sys.argv[1], sys.argv[2]
PORT = ports.get(sys.argv[3] if len(sys.argv) > 3 else '2018')
D = bytearray(open(src, 'rb').read())
if D[:4] == b'JDLZ':
    raise SystemExit('GlobalB is compressed; decompress first')
chunk = None
for a, b, p, s in ug2.chunks(bytes(D), 0, len(D), 0, []):
    if b == 0x34600:
        chunk = (p + 8, s)
assert chunk
base, size = chunk
recs = {}
for off in range(base + 8, base + size, REC):
    name = bytes(D[off:off + 32]).split(b'\0')[0].decode()
    recs[name] = off
F, C, L = recs[PORT['ug2']], recs['COROLLA'], recs['LANCEREVO8']
before = bytes(D[F:F + REC])


def copy(src_off, a, b):
    D[F + a:F + b] = D[src_off + a:src_off + b]


def setf(o, v):
    struct.pack_into('<f', D, F + o, v)


# --- handling from the Lancer Evo VIII
# v3: rim size bytes (220) stay the Focus ones: a saved Focus with 16" rims must remain valid
copy(L, 272, 288)            # per-axle values next to the wheels
for w in range(4):           # the two unknown per-wheel values (keep the Lancer ones)
    copy(L, 288 + 48 * w + 28, 288 + 48 * w + 36)
copy(L, 480, 704)            # tyres, mass, inertia, suspension
copy(L, 880, 992)            # grip/brake/aero block
copy(L, 1616, 2032)          # upgrade tables: tyres, suspension, steering, brakes
# --- engine and gearbox from the Corolla
copy(C, 704, 880)            # stock transmission + engine + turbo curves
copy(C, 992, 1616)           # upgrade tables: engine, turbo, transmission
# --- Corolla engine scaled to 248 cv: torque arrays in kN*m (the rpm steps 1380/1444/1508 and the
# transmission tables in between are left alone)
TARGET_KW = 248 * 0.73549875
MASS = 1.63


def peak_kw(rec):
    torque = struct.unpack_from('<9f', D, rec + 784)
    max_rpm = struct.unpack_from('<f', D, rec + 776)[0]
    return max(t * max_rpm * k / 8 * 2 * math.pi / 60 for k, t in enumerate(torque))


POWER = TARGET_KW / peak_kw(C)
TORQUE_ARRAYS = [(784, 820),    # stock torque curve, 9 points
                 (820, 856),    # stock turbo curve, 9 points
                 (992, 1100),   # engine / turbo upgrade increments, 3 x 9 points
                 (1328, 1376), (1392, 1440), (1456, 1504), (1520, 1568),   # upgrade curves, 12 points
                 (1572, 1604)]  # turbo upgrade curve
for a, b in TORQUE_ARRAYS:
    for o in range(a, b, 4):
        setf(o, struct.unpack_from('<f', D, C + o)[0] * POWER)
# 2018 copies the Lancer split (0.5, AWD). 2012 forces 1.0 (FWD) on the same chassis.
for o in (720, 1136, 1200, 1264):
    if PORT['drive'] == 'FWD':
        setf(o, PORT['split'])
    else:
        copy(L, o, o + 4)

# --- Fusion geometry
FX, RX, WY = 1.431, -1.311, 0.78
wheels = [(FX, WY), (FX, -WY), (RX, -WY), (RX, WY)]   # same order/signs as the stock records
for i, (x, y) in enumerate(wheels):
    struct.pack_into('<2f', D, F + 288 + 48 * i, x, y)
mass = MASS
length, width, height = 4.73, 1.85, 1.46
struct.pack_into('<4f', D, F + 544, mass, length, width, height)
ix = mass / 12 * (width ** 2 + height ** 2)
iy = mass / 12 * (length ** 2 + height ** 2)
iz = mass / 12 * (length ** 2 + width ** 2)
setf(560, ix); setf(580, iy); setf(600, iz)
open(dst, 'wb').write(D)
after = bytes(D[F:F + REC])
changed = [o for o in range(0, REC, 4) if before[o:o + 4] != after[o:o + 4]]
report = dict(port=PORT['id'], slot=PORT['ug2'], drive=PORT['drive'], record_offset=F, changed_fields=len(changed), mass=mass, inertia=[ix, iy, iz],
              wheels=wheels, wheel_z=struct.unpack_from('<f', D, F + 296)[0],
              tyre_radius_width=struct.unpack_from('<2f', D, F + 304),
              torque_scale=POWER, peak_cv=peak_kw(F) / 0.73549875, torque_stock=struct.unpack_from('<9f', D, F + 784),
              torque_split=struct.unpack_from('<f', D, F + 720)[0],
              redline=struct.unpack_from('<2f', D, F + 772),
              gears=struct.unpack_from('<6f', D, F + 736))
print(json.dumps(report, indent=1))
