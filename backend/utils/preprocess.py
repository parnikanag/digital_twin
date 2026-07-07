def preprocess(data):
    """Extract all 8 ENB2012 feature values in the correct column order."""
    keys = [
        "relative_compactness",   # X1
        "surface_area",           # X2
        "wall_area",              # X3
        "roof_area",              # X4
        "overall_height",         # X5
        "orientation",            # X6
        "glazing_area",           # X7
        "glazing_area_distribution",  # X8
    ]
    return [data[k] for k in keys]
