import numpy as np

def MC(hash_index, DH, coords, shell_labels):
    """
    Compute MC = (radius, angle, shell_id)
    for the hash at position hash_index.
    """

    # --- 1. Radius (curvature distance from puzzle160 = index 2)
    puzzle_idx = 2
    radius = DH[hash_index, puzzle_idx]

    # --- 2. Angle using Atlas coordinates (atan2)
    x, y, z = coords[hash_index]
    angle = np.degrees(np.arctan2(y, x))

    # --- 3. Shell label (your literal power-slice classification)
    shell = shell_labels[hash_index]

    return {
        "MC_radius": radius,
        "MC_angle_deg": angle,
        "MC_shell": shell
    }

# Example shell labels:
shell_labels = [
    "2^159",
    "2^159+80",
    "puzzle160",
    "2^159.5",
    "2^160",
    "2^160-80",
    "2^160-81",
    "-half",
    "+half",
    "-quarter",
    "+quarter",
    "-eighth",
    "+eighth",
    "-81",
    "+81"
]
