"""Procedural latte-and-croissant flat-lay rendered as a PNG."""

from __future__ import annotations

import os
import struct
import zlib
from math import atan2, cos, hypot, pi, sin, tau


SIZE = 1280
SAMPLES = ((-0.25, -0.25), (0.25, -0.25), (-0.25, 0.25), (0.25, 0.25))


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return low if value < low else high if value > high else value


def mix(first: float, second: float, amount: float) -> float:
    return first + (second - first) * amount


def mix3(first: tuple, second: tuple, amount: float) -> tuple:
    amount = clamp(amount)
    return tuple(first[index] + (second[index] - first[index]) * amount for index in range(3))


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    amount = clamp((value - edge0) / (edge1 - edge0))
    return amount * amount * (3.0 - 2.0 * amount)


def ellipse_distance(x: float, y: float, rx: float, ry: float) -> float:
    scale = hypot(x / rx, y / ry)
    return (scale - 1.0) * min(rx, ry)


def hash01(x: float, y: float, salt: float) -> float:
    noise = sin(x * 127.1 + y * 311.7 + salt * 74.3) * 43758.5453
    return noise - int(noise)


def write_png(path: str, width: int, height: int, rows: list[bytes]) -> None:
    raw = b"".join(b"\x00" + row for row in rows)

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    with open(path, "wb") as image_file:
        image_file.write(b"\x89PNG\r\n\x1a\n")
        image_file.write(chunk(b"IHDR", header))
        image_file.write(chunk(b"IDAT", zlib.compress(raw, 9)))
        image_file.write(chunk(b"IEND", b""))


def rounded_rectangle_distance(x: float, y: float, half: tuple[float, float], radius: float) -> float:
    qx = abs(x) - (half[0] - radius)
    qy = abs(y) - (half[1] - radius)
    return hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - radius


def coffee_art(x: float, y: float) -> float:
    stem_x = 0.14 * sin(y * 1.35 + 0.3)
    stem_width = 0.026 + 0.020 * smoothstep(0.68, -0.74, y)
    stem = smoothstep(stem_width + 0.008, stem_width - 0.008, abs(x - stem_x))
    stem *= smoothstep(-0.82, -0.71, y) * smoothstep(0.77, 0.66, y)

    veins = 0.0
    centers = (-0.55, -0.22, 0.11, 0.44)
    widths = (0.21, 0.19, 0.17, 0.14)
    for center, spread in zip(centers, widths):
        vertical = abs(y - center) / 0.115
        if vertical < 1.0:
            profile = 1.0 - vertical * vertical
            thickness = 0.038 * profile + 0.008
            for side in (-1.0, 1.0):
                target_x = stem_x + side * spread * profile
                veins = max(veins, smoothstep(thickness + 0.006, thickness - 0.006, abs(x - target_x)))

    return clamp(stem + veins * 0.85)


def bean_alpha(x: float, y: float, angle: float) -> float:
    u = x * cos(angle) + y * sin(angle)
    v = -x * sin(angle) + y * cos(angle)
    return smoothstep(0.006, -0.006, ellipse_distance(u, v, 0.072, 0.048))


def scene(u: float, v: float) -> tuple:
    linen = mix3((0.846, 0.769, 0.648), (0.950, 0.900, 0.803), smoothstep(1.35, -1.15, u + v))
    linen = mix3(linen, (0.799, 0.713, 0.578), 0.14 + 0.13 * sin(u * 118.0))
    linen = mix3(linen, (0.891, 0.823, 0.701), 0.10 + 0.12 * sin(v * 104.0))
    linen = mix3(linen, (0.685, 0.587, 0.458), smoothstep(0.42, 1.30, hypot(u, v)) * 0.70)

    napkin = rounded_rectangle_distance(u + 0.18, v - 0.12, (0.77, 0.72), 0.16)
    napkin_alpha = smoothstep(0.012, -0.012, napkin)
    napkin_color = mix3((0.870, 0.830, 0.755), (0.960, 0.931, 0.873), smoothstep(0.72, -0.66, u + v))
    napkin_color = mix3(napkin_color, (0.830, 0.784, 0.705), 0.08 + 0.06 * sin(u * 90.0))
    linen = mix3(linen, napkin_color, napkin_alpha * 0.92)

    relative_x, relative_y = u + 0.18, v - 0.18
    saucer_shadow = smoothstep(0.12, -0.05, hypot(relative_x * 0.94, relative_y * 0.88 + 0.06) - 0.60)
    linen = mix3(linen, (0.455, 0.375, 0.297), saucer_shadow * 0.24)

    saucer_distance = hypot(relative_x, relative_y * 1.012)
    saucer = smoothstep(0.008, -0.008, saucer_distance - 0.56)
    saucer_color = mix3((0.836, 0.815, 0.779), (0.972, 0.959, 0.937), smoothstep(0.56, -0.05, saucer_distance))
    saucer_color = mix3(saucer_color, (0.733, 0.709, 0.672), smoothstep(0.33, 0.45, saucer_distance))
    saucer_color = mix3(saucer_color, (0.871, 0.851, 0.818), smoothstep(0.48, 0.54, saucer_distance))
    linen = mix3(linen, saucer_color, saucer)

    cup_distance = hypot(relative_x, relative_y)
    cup = smoothstep(0.007, -0.007, cup_distance - 0.335)
    cup_color = mix3((0.818, 0.795, 0.758), (0.979, 0.968, 0.948), smoothstep(0.34, -0.18, cup_distance))
    cup_color = mix3(cup_color, (0.654, 0.629, 0.597), smoothstep(0.255, 0.335, cup_distance) * 0.64)
    linen = mix3(linen, cup_color, cup)

    coffee = smoothstep(0.004, -0.004, cup_distance - 0.268)
    crema = smoothstep(0.255, 0.155, cup_distance)
    coffee_color = mix3((0.484, 0.280, 0.171), (0.779, 0.578, 0.407), crema)
    coffee_color = mix3(coffee_color, (0.350, 0.205, 0.126), smoothstep(0.205, 0.268, cup_distance) * 0.70)
    coffee_color = mix3(coffee_color, (0.630, 0.424, 0.287), 0.18 * smoothstep(0.0, 0.7, sin(cup_distance * 28.0 + atan2(relative_y, relative_x) * 7.0)))

    art_x, art_y = relative_x / 0.265, relative_y / 0.265
    art = coffee_art(art_x, art_y) * smoothstep(0.955, 0.88, hypot(art_x, art_y))
    coffee_color = mix3(coffee_color, (0.975, 0.930, 0.834), art * 0.91)
    linen = mix3(linen, coffee_color, coffee)

    rim_highlight = smoothstep(0.295, 0.315, cup_distance) * smoothstep(0.345, 0.330, cup_distance)
    rim_highlight *= smoothstep(0.55, 0.0, (relative_x + relative_y + 0.60) / 1.2)
    linen = mix3(linen, (0.995, 0.992, 0.978), rim_highlight * 0.82)

    crescent_x, crescent_y = u - 0.46, v + 0.34
    croissant_angle = atan2(crescent_y, crescent_x)
    angular_gap = abs((croissant_angle - 1.62 + pi) % tau - pi)
    croissant_radius = hypot(crescent_x, crescent_y)
    ridge = 0.024 * sin(croissant_angle * 13.0)
    ring_distance = abs(croissant_radius - (0.48 + ridge))
    croissant = smoothstep(0.010, -0.010, ring_distance - 0.125) * smoothstep(1.08, 0.91, angular_gap)
    croissant_color = mix3((0.635, 0.360, 0.158), (0.945, 0.724, 0.429), smoothstep(0.36, 0.61, croissant_radius))
    croissant_color = mix3(croissant_color, (0.495, 0.264, 0.110), 0.24 * smoothstep(0.5, 1.0, hash01(int(u * 260.0), int(v * 260.0), 11.0)))
    croissant_color = mix3(croissant_color, (0.991, 0.914, 0.761), 0.20 * smoothstep(0.49, 0.61, croissant_radius))
    linen = mix3(linen, (0.418, 0.340, 0.266), smoothstep(0.13, -0.03, hypot(crescent_x, crescent_y - 0.10) - 0.52) * 0.20)
    linen = mix3(linen, croissant_color, croissant * 0.98)

    beans = ((-0.66, -0.43, 0.25), (-0.20, -0.61, -0.30), (0.69, 0.27, 0.65))
    for index, (bx, by, angle) in enumerate(beans):
        bean = bean_alpha(u - bx, v - by, angle)
        if bean > 0.0:
            local_x = (u - bx) * cos(angle) + (v - by) * sin(angle)
            crease = smoothstep(0.020, 0.000, abs(local_x + 0.012 * sin((v - by) * 35.0)))
            bean_color = mix3((0.262, 0.160, 0.104), (0.402, 0.250, 0.155), hash01(index, int(u * 120.0), int(v * 120.0)))
            bean_color = mix3(bean_color, (0.135, 0.084, 0.058), crease * 0.82)
            linen = mix3(linen, bean_color, bean)

    sparkle = hash01(u * 340.0, v * 340.0, 5.0)
    result = mix3(linen, (1.0, 0.973, 0.909), clamp(sparkle - 0.88) * 0.10)
    result = mix3(result, (0.467, 0.382, 0.297), smoothstep(0.60, 1.22, hypot(u + 0.08, v + 0.04)) * 0.34)
    return result


def render() -> list[bytes]:
    rows: list[bytes] = []
    scale = SIZE / 2.0
    for pixel_y in range(SIZE):
        row = bytearray()
        for pixel_x in range(SIZE):
            red = green = blue = 0.0
            for offset_x, offset_y in SAMPLES:
                coordinate_x = (pixel_x + offset_x) / scale - 1.0
                coordinate_y = (pixel_y + offset_y) / scale - 1.0
                sample = scene(coordinate_x, coordinate_y)
                red += sample[0]
                green += sample[1]
                blue += sample[2]
            row += bytes((
                int(clamp(red / 4.0) * 255.0 + 0.5),
                int(clamp(green / 4.0) * 255.0 + 0.5),
                int(clamp(blue / 4.0) * 255.0 + 0.5),
            ))
        rows.append(bytes(row))
    return rows


def main() -> None:
    output_directory = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(output_directory, exist_ok=True)
    write_png(os.path.join(output_directory, "entry.png"), SIZE, SIZE, render())


if __name__ == "__main__":
    main()
