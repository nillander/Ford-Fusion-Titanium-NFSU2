def bh(s):
    v=0xFFFFFFFF
    for c in s.encode(): v=(v*33+c)&0xFFFFFFFF
    return v
