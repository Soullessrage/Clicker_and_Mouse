"""Mathematical generators for reusable built-in paths."""

import math
import random
from typing import List, Tuple

Point = Tuple[int, int]


class ShapePaths:
    """Generate closed paths centered on the origin."""

    @staticmethod
    def circle(radius: int = 120, samples: int = 96) -> List[Point]:
        if radius <= 0 or samples < 3:
            raise ValueError("A circle requires a positive radius and at least three samples")
        return [
            (round(radius * math.cos(2 * math.pi * index / samples)),
             round(radius * math.sin(2 * math.pi * index / samples)))
            for index in range(samples + 1)
        ]

    @staticmethod
    def square(side: int = 220, samples_per_side: int = 24) -> List[Point]:
        if side <= 0 or samples_per_side < 1:
            raise ValueError("A square requires a positive side and at least one sample per side")
        half = side / 2
        corners = [(-half, -half), (half, -half), (half, half), (-half, half), (-half, -half)]
        points: List[Point] = []
        for start, end in zip(corners, corners[1:]):
            for index in range(samples_per_side):
                fraction = index / samples_per_side
                points.append((
                    round(start[0] + (end[0] - start[0]) * fraction),
                    round(start[1] + (end[1] - start[1]) * fraction),
                ))
        points.append((round(corners[-1][0]), round(corners[-1][1])))
        return points

    @staticmethod
    def triangle(side: int = 260, samples_per_side: int = 32) -> List[Point]:
        if side <= 0 or samples_per_side < 1:
            raise ValueError("A triangle requires a positive side and at least one sample per side")
        height = side * math.sqrt(3) / 2
        corners = [
            (0.0, -2 * height / 3),
            (-side / 2, height / 3),
            (side / 2, height / 3),
            (0.0, -2 * height / 3),
        ]
        points: List[Point] = []
        for start, end in zip(corners, corners[1:]):
            for index in range(samples_per_side):
                fraction = index / samples_per_side
                points.append((
                    round(start[0] + (end[0] - start[0]) * fraction),
                    round(start[1] + (end[1] - start[1]) * fraction),
                ))
        points.append((round(corners[-1][0]), round(corners[-1][1])))
        return points

    @staticmethod
    def random_path(width: int, height: int, waypoints: int = 32, margin: int = 24) -> List[Point]:
        """Generate random screen positions for a continuously looping path."""
        if width < 1 or height < 1 or waypoints < 2:
            raise ValueError("A random path requires a positive screen size and at least two waypoints")
        safe_margin = max(0, min(margin, (width - 1) // 2, (height - 1) // 2))
        random_source = random.SystemRandom()
        points = [
            (
                random_source.randint(safe_margin, max(safe_margin, width - 1 - safe_margin)),
                random_source.randint(safe_margin, max(safe_margin, height - 1 - safe_margin)),
            )
            for _ in range(waypoints)
        ]
        points.append(points[0])
        return points