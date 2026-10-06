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
        'split': 0.0,          # offset 720 is the share sent to the rear axle: retail FWD cars store 0.0
        # Budget knobs (see build.py). The 2012 front lamps and rear end are about 2.5x heavier than the 2018
        # ones at every LOD; these settings keep each solid under 21,500 triangles.
        'lamps': dict(head='D', head_glass='C', brake='D', brake_glass='D'),
        'lens': 'outward',
        'valance': 'inward',
        'rear_in': 'trunk',
        'rear_x': -1.95,
        'body_b_target': 15600,
        'trunk_lod': 'B',
        'outer_brake_in': 'trunk',
        'nose_in': 'body',
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
