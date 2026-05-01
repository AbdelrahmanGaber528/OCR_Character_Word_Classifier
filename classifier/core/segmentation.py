"""
shared/segmentation.py
Split a word image into individual character crops via vertical projection.
"""
import io
import numpy as np
from PIL import Image as PILImage


def segment_word(image_bytes: bytes, gap_tolerance: int = 3, padding: int = 4) -> list:
    """
    Segment a word image into sorted character crops.

    Strategy
    --------
    1. Binarise (ink = 1, background = 0)
    2. Sum ink pixels per column → vertical projection
    3. Find contiguous ink-column runs → one crop per run
    4. Merge runs whose gap ≤ gap_tolerance (handles touching letters)
    5. Add horizontal padding, sort left → right

    Returns a list of PIL Images.
    If no segments found, returns [original image] as fallback.
    """
    img  = PILImage.open(io.BytesIO(image_bytes)).convert("L")
    arr  = np.array(img)
    h, w = arr.shape

    ink    = (arr < 128).astype(np.uint8)
    proj   = ink.sum(axis=0)
    in_ink = proj > 0

    starts, ends = [], []
    for c in range(w):
        if in_ink[c] and (c == 0 or not in_ink[c - 1]):
            starts.append(c)
        if in_ink[c] and (c == w - 1 or not in_ink[c + 1]):
            ends.append(c)

    if not starts:
        return [img]

    segs = list(zip(starts, ends))

    # merge close segments
    merged = [list(segs[0])]
    for s, e in segs[1:]:
        if s - merged[-1][1] <= gap_tolerance:
            merged[-1][1] = e
        else:
            merged.append([s, e])

    crops = []
    for x0, x1 in merged:
        left  = max(0, x0 - padding)
        right = min(w, x1 + padding + 1)
        crops.append(img.crop((left, 0, right, h)))

    return crops or [img]