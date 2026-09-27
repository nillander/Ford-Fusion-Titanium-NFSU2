"""Patches the FOCUS CarTypeInfo (chunk 0x34600, 2192-byte records) in GlobalB.lzc.

Engine and gearbox: Toyota COROLLA with every torque curve x1.2 (stock, turbo and upgrades), so the
power is the Corolla's +20 % at every rpm and upgrade level.  Drivetrain: AWD (torque split 0.5, as
LANCEREVO8).  Chassis, tyres, suspension, steering, brakes and mass (1.40 t, heavier than the Focus
1.15 t and the Corolla 0.97 t): LANCEREVO8.  Wheel X/Y, body dimensions and inertia: Fusion geometry
(long car -> larger yaw inertia, 2.74 m wheelbase).  Wheel Z, tyre radius and width stay as they are
in the input (the Escort values were approved in the game).
"""
import struct, sys, json
import ug2

REC = 2192
src, dst = sys.argv[1], sys.argv[2]
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
F, C, L = recs['FOCUS'], recs['COROLLA'], recs['LANCEREVO8']
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
# --- Corolla power +20 %: torque arrays in kN*m (the rpm steps 1380/1444/1508 and the transmission
# tables in between are left alone)
POWER = 1.2
TORQUE_ARRAYS = [(784, 820),    # stock torque curve, 9 points
                 (820, 856),    # stock turbo curve, 9 points
                 (992, 1100),   # engine / turbo upgrade increments, 3 x 9 points
                 (1328, 1376), (1392, 1440), (1456, 1504), (1520, 1568),   # upgrade curves, 12 points
                 (1572, 1604)]  # turbo upgrade curve
for a, b in TORQUE_ARRAYS:
    for o in range(a, b, 4):
        setf(o, struct.unpack_from('<f', D, C + o)[0] * POWER)
# --- AWD: torque split 0.5 at stock and at the three upgrade levels (Lancer value)
for o in (720, 1136, 1200, 1264):
    copy(L, o, o + 4)

# --- Fusion geometry
FX, RX, WY = 1.431, -1.311, 0.78
wheels = [(FX, WY), (FX, -WY), (RX, -WY), (RX, WY)]   # same order/signs as the stock records
for i, (x, y) in enumerate(wheels):
    struct.pack_into('<2f', D, F + 288 + 48 * i, x, y)
mass = struct.unpack_from('<f', D, L + 544)[0]
assert mass > max(struct.unpack_from('<f', before, 544)[0], struct.unpack_from('<f', D, C + 544)[0])
length, width, height = 4.73, 1.85, 1.46
struct.pack_into('<4f', D, F + 544, mass, length, width, height)
ix = mass / 12 * (width ** 2 + height ** 2)
iy = mass / 12 * (length ** 2 + height ** 2)
iz = mass / 12 * (length ** 2 + width ** 2)
setf(560, ix); setf(580, iy); setf(600, iz)
open(dst, 'wb').write(D)
after = bytes(D[F:F + REC])
changed = [o for o in range(0, REC, 4) if before[o:o + 4] != after[o:o + 4]]
report = dict(record_offset=F, changed_fields=len(changed), mass=mass, inertia=[ix, iy, iz],
              wheels=wheels, wheel_z=struct.unpack_from('<f', D, F + 296)[0],
              tyre_radius_width=struct.unpack_from('<2f', D, F + 304),
              torque_scale=POWER, torque_stock=struct.unpack_from('<9f', D, F + 784),
              torque_split=struct.unpack_from('<f', D, F + 720)[0],
              redline=struct.unpack_from('<2f', D, F + 772),
              gears=struct.unpack_from('<6f', D, F + 736))
print(json.dumps(report, indent=1))
