import sys

# 1. Define the 2D String Matrix representing the columns from the Gortyn Code image
# Each row represents consecutive lines inside an epigraphic text column
gortyn_column_matrix = [
    ["ΘΕΟΙ", "ΤΑΝΠΑΝΤΩΝΔΙΚΑΝ", "ΚΡΙΝΕΝΤΟΝΔΙΚΑΣΤΑΝ", "ΚΑΤΑΤΑΓΡΑΜΜΑΤΑ"],  # Line 0: L-to-R
    ["ΣΑΝΕΜΠΑΛΙΝΡΑΓΤΑΤΑΚΑ", "ΝΟΜΟΙΣΔΕΚΑΔΕΓΡΑΜΜΕ", "ΝΟΝΕΣΤΙ"],          # Line 1: R-to-L (Archaic)
    ["ΑΙΔΕΜΗΓΕΓΡΑΠΤΑΙΚΡΙ", "ΝΕΝΚΑΤΑΠΑΝΤΑΔΙΚΑΝ", "ΑΥΤΟΝΟΜΟΝ"]          # Line 2: L-to-R
]

def parse_boustrophedon_matrix(matrix):
    """
    Applies an inversion filter across alternating row indices 
    to normalize the reading direction of the boustrophedon text.
    """
    normalized_columns = []
    
    for col_idx, column in enumerate(matrix):
        normalized_lines = []
        print(f"[+] Processing Column {col_idx + 1} Text Boundaries:")
        
        for line_idx, line in enumerate(column):
            # Check for alternating boustrophedon direction
            # Even indices (0, 2, 4...) read Left-to-Right naturally
            if line_idx % 2 == 0:
                direction = "Left-to-Right"
                processed_line = line
            # Odd indices (1, 3, 5...) read Right-to-Left and must be inverted
            else:
                direction = "Right-to-Left [INVERTING]"
                # Invert the character string array
                processed_line = line[::-1]
                
            print(f"    Line {line_idx}: Reading {direction} -> {processed_line}")
            normalized_lines.append(processed_line)
            
        normalized_columns.append(normalized_lines)
    return normalized_columns

print("[+] Initializing Boustrophedon Inversion Filter...\n")
parsed_data = parse_boustrophedon_matrix(gortyn_column_matrix)

print("\n[+] Full Normalized Legal Inscription Matrix Reconstructed Successfully.")
