# Script to compute weighted sums of all descending compositions of 71 using the TDAD pattern.
# TDAD (Triple, Double, Add, Double) multipliers repeat for each term in the composition.
# For each composition (a sequence of positive integers summing to 71 in non-increasing order),
# the script multiplies the first term's puzzle value by 3, second term's value by 2, third by 1, fourth by 2, then repeats (3,2,1,2,...).
# It then sums these weighted values to get a total for that composition.
# All results are written to an output file, each line formatted as "composition: total".
# Any totals matching or near matching Puzzle 71's target sum (if known) are flagged in the output.

# Puzzle values mapping (puzzle number -> its value) as extracted from ALIGNED.txt.
# This dictionary provides the final value for each puzzle number 1 through 70.
puzzle_values = {
    1: 1,
    2: 3,
    3: 7,
    4: 8,
    5: 21,
    6: 49,
    7: 76,
    8: 224,
    9: 467,
    10: 514,
    11: 1155,
    12: 2683,
    13: 5216,
    14: 10544,
    15: 26867,
    16: 51510,
    17: 95823,
    18: 198669,
    19: 357535,
    20: 863317,
    21: 1811764,
    22: 3007503,
    23: 5598802,
    24: 14428676,
    25: 33185509,
    26: 54538862,
    27: 111949941,
    28: 227634408,
    29: 400708894,
    30: 1033162084,
    31: 2102388551,
    32: 3093472814,
    33: 7137437912,
    34: 14133072157,
    35: 20112871792,
    36: 42387769980,
    37: 100251560595,
    38: 146971536592,
    39: 323724968937,
    40: 1003651412950,
    41: 1458252205147,
    42: 2895374552463,
    43: 7409811047825,
    44: 15404761757071,
    45: 19996463086597,
    46: 51408670348612,
    47: 119666659114170,
    48: 191206974700443,
    49: 409118905032525,
    50: 611140496167764,
    51: 2058769515153876,
    52: 4216495639600700,
    53: 6763683971478124,
    54: 9974455244496707,
    55: 30045390491869460,
    56: 44218742292676575,
    57: 138245758910846492,
    58: 199976667976342049,
    59: 525070384258266191,
    60: 1135041350219496382,
    61: 1425787542618654982,
    62: 3908372542507822062,
    63: 8993229949524469768,
    64: 17799667357578236628,
    65: 30568377312064202855,
    66: 46346217550346335726,
    67: 132656943602386256302,
    68: 219898266213316039825,
    69: 297274491920375905804,
    70: 970436974005023690481
}
# (Puzzle 71's value is not included above as it may not be finalized; we use it only for comparison if available.)

# Puzzle 71 target sum (if known). This is used for comparison to flag matching or near-matching totals.
puzzle71_target = 1411488254391826260559  # Known target sum for puzzle 71 (from available data). Change if needed.

# Define what "near-matching" means: here we use a threshold for closeness.
# We'll flag a composition if its total is exactly equal to puzzle71_target,
# or if the difference is within a small tolerance (e.g. 1e15) which is about 0.07% of the target.
near_threshold = 10**15

# Output file to store the results
output_filename = "composition_sums.txt"
out_file = open(output_filename, "w")

# Counter for number of compositions processed
count = 0

# Define multipliers pattern for TDAD: repeating [3, 2, 1, 2]
pattern = [3, 2, 1, 2]

# Recursive function to generate all descending compositions of a given sum.
def generate_compositions(remain, max_val, comp_list, index, current_sum):
    """
    Generate all descending compositions of 'remain' (remaining sum) with largest part <= max_val.
    comp_list holds the current composition being built.
    index is the 0-based position in the composition (to determine the multiplier from TDAD pattern).
    current_sum accumulates the weighted sum for the current composition so far.
    """
    global count
    if remain == 0:
        # We have a complete composition that sums to 71.
        # Format the composition and its total, then write to file.
        total = current_sum
        # Build a string for the composition, e.g. "a + b + c".
        comp_str = " + ".join(map(str, comp_list))
        # Determine if this total matches or is near the Puzzle 71 target.
        flag = ""
        if puzzle71_target is not None:
            if total == puzzle71_target:
                flag = " <-- match Puzzle 71 target"
            elif abs(total - puzzle71_target) <= near_threshold:
                flag = " <-- near match Puzzle 71 target"
        # Write the line "composition: total" (with any flag if applicable).
        out_file.write(f"{comp_str}: {total}{flag}\n")
        count += 1
    else:
        # Try all possible next parts for the composition, from max_val down to 1.
        for x in range(min(max_val, remain), 0, -1):
            # Only proceed if we have a puzzle value for this part (should be 1..70).
            if x not in puzzle_values:
                continue  # Skip any part >70 (no puzzle value known for 71 or above).
            # Determine the multiplier for this position (index) in the composition.
            multiplier = pattern[index % len(pattern)]
            # Calculate new total including this part's contribution.
            new_total = current_sum + multiplier * puzzle_values[x]
            # Add this part to the current composition and recurse.
            comp_list.append(x)
            generate_compositions(remain - x, x, comp_list, index + 1, new_total)
            # Backtrack: remove the last added part before trying the next possibility.
            comp_list.pop()

# Start generating compositions of 71.
generate_compositions(remain=71, max_val=70, comp_list=[], index=0, current_sum=0)

# Close the output file.
out_file.close()

# Print a summary message.
print(f"Done! Generated {count} compositions of 71. Results saved to {output_filename}.")
