"""Substitution table for the two Underground 2 ports.

Both ports share the 2018 geometry pipeline (part split, clip, glass, decals, vinyl).
The 2012 run reads the Cobalt SS archive and writes the Focus slot; only the
drivetrain split differs in the GlobalB patch.
"""

PORTS = {
    '2018': {
        'id': '2018',
        'mw': 'MUSTANGGT',
        'ug2': 'MUSTANGGT',
        'zip': 'Fusion2018_AWD_MW2005.zip',
        'drive': 'AWD',
        'split': 0.5,
    },
    '2012': {
        'id': '2012',
        'mw': 'COBALTSS',
        'ug2': 'FOCUS',
        'zip': 'Fusion2012_FWD_MW2005.zip',
        'drive': 'FWD',
        'split': 1.0,
    },
}

# DXT headers plus shadow and neon pixels. This file is the v9 that proved which
# parts the Focus slot draws. Both ports borrow that structure; neither reads the
# deleted Escort archive.
TEMPLATE = 'CARS/MUSTANGGT/TEXTURES.BIN'


def get(port_id='2018'):
    key = str(port_id)
    if key not in PORTS:
        raise SystemExit('port must be 2018 or 2012, got %s' % key)
    return PORTS[key]
