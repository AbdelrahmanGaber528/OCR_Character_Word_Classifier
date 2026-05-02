
# doesn't work ---------------------------------------------------------- doesn't work ---------------------------------------------------------- doesn't work ----------------------------------------------------------

import io
import numpy as np
from PIL import Image as PILImage


def segment_word(image_bytes: bytes, padding: int = 4) -> list:
    """
    Split a word image into sorted character crops via vertical projection.
    Returns list of PIL Images.
    """
    img  = PILImage.open(io.BytesIO(image_bytes)).convert("L")
    arr  = np.array(img)
    h, w = arr.shape

    is_light_bg = arr.mean() > 127
    binary   = (arr < 128).astype(np.uint8) if is_light_bg else (arr > 128).astype(np.uint8)
    col_proj = binary.sum(axis=0)
    in_char  = col_proj > 0

    starts, ends = [], []
    for c in range(w):
        if in_char[c] and (c == 0 or not in_char[c - 1]):
            starts.append(c)
        if in_char[c] and (c == w - 1 or not in_char[c + 1]):
            ends.append(c)

    if not starts:
        return [img]

    segments = list(zip(starts, ends))
    merged   = [segments[0]]
    for seg in segments[1:]:
        if seg[0] - merged[-1][1] <= 3:
            merged[-1] = (merged[-1][0], seg[1])
        else:
            merged.append(seg)

    return [
        img.crop((max(0, x0 - padding), 0, min(w, x1 + padding + 1), h))
        for x0, x1 in merged
    ] or [img]