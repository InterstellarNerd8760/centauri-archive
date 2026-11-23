"""Generate the original calibration raster using integer arithmetic only."""
from math import isqrt

WIDTH = 1024


def plate():
    pixels = bytearray()
    for y in range(WIDTH):
        for x in range(WIDTH):
            left = isqrt((x - 310) ** 2 + (y - 450) ** 2)
            right = isqrt((x - 710) ** 2 + (y - 450) ** 2)
            level = 40 + 85 * ((left // 22) % 2) + 125 * ((right // 22) % 2)
            if y >= 960:
                level = x * 255 // 1023
            elif x < 64 and y < 64:
                level = 0 if x < 24 and y < 24 else 255
            pixels.append(level)
    return b"P5\n1024 1024\n255\n" + pixels
