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
        'solid_tail': True,
        'fog_lod': 'A',
        'wheel_donor': 'FOCUS',
        # v10.15 opened with the repaired trim/lenses; keep the lighter approved lid.
        'trunk_paint_target': 6000,
    },
    '2012': {
        'id': '2012',
        'mw': 'COBALTSS',
        'ug2': 'FOCUS',
        'zip': 'Fusion2012_FWD_MW2005.zip',
        'drive': 'FWD',
        'split': 0.0,          # offset 720 is the share sent to the rear axle: retail FWD cars store 0.0
        'opaque_reflectors': True,  # lower rear pair: reuse the 2018 MISC/DULLPLASTIC red finish
        # Budget knobs (see build.py). The 2012 front lamps and rear end are about 2.5x heavier than the 2018
        # ones at every LOD; these settings keep each solid under 21,500 triangles.
        'lamps': dict(head='D', head_glass='C', brake='D', brake_glass='D'),
        'rear_in': 'trunk',
        'rear_x': -1.95,
        'body_b_target': 15200,
        'rear_lod': 'B',
        'base_dec': 0.75,
        'trunk_lod': 'B',
        'outer_brake_in': 'trunk',
        'nose_in': 'body',
        'tex_cells': {'KIT00_HEADLIGHT': [((4, 4), (5, 4), 0.65)]},
        # v11: names the game binds (see TEX_ALIAS in build.py). FOCUS_KIT00_HEADLIGHT_GLASS_OFF is the retail
        # Focus headlight lens; SIDELIGHT is drawn by the retail BASE; the other two are unused car slots.
        # v11.1: HEADLIGHT_GLASS (41 small BASE triangles) stays unbound to save memory.
        'tex_alias': {'KIT00_HEADLIGHT': 'SIDELIGHT', 'HEADLIGHT_LENS': 'KIT00_HEADLIGHT_GLASS_OFF',
                      'BRAKELIGHT_GLASS': 'CENTRE_BRAKELIGHT'},
        'tex_size': {'HEADLIGHT_LENS': 128, 'BRAKELIGHT_GLASS': 128, 'BADGING': 256},
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
