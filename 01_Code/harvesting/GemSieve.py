import math
import sys

# Standard secp256k1 Parameters
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

# Base point G coordinates for verification references if needed
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

class ReversalTestPlan:
    def __init__(self, puzzle_height, target_x=None, target_y=None, solved_priv_key=None):
        self.height = puzzle_height
        self.target_x = target_x
        self.target_y = target_y
        self.solved_key = solved_priv_key
        
        # Calculate standard range and delta variables
        self.range_floor = 2**(puzzle_height - 1)
        self.range_ceiling = (2**puzzle_height) - 1
        self.D = self.range_ceiling - self.range_floor
        self.mid = self.range_floor + (self.D // 2)
        
    def generate_lanes(self):
        """
        Implements the operational arithmetic footer rules:
        ン D／8 中時
        """
        d_div_8 = self.D // 8  # 3-bit logical shift right (2^k / 8)
        
        lanes = {
            "Lane A (Counter-Drift)": self.mid - d_div_8,
            "Lane B (Center Balance)": self.mid,
            "Lane C (Accumulation)": self.mid + d_div_8
        }
        return lanes

    def evaluate_lane(self, name, scalar_candidate):
        """
        Calculates all measurable outputs required by the ledger schema matrix.
        """
        metrics = {
            "Lane Description": name,
            "Scalar Candidate (Hex)": f"0x{scalar_candidate:X}",
            "Log2 Normalization": round(math.log2(scalar_candidate), 4) if scalar_candidate > 0 else 0
        }
        
        # 1. D/8 Operator Proximity
        metrics["Distance to Midpoint"] = scalar_candidate - self.mid
        
        # 2. N - 8 Mirror / Reflection Checksum Context
        # Simulates where this candidate sits relative to the upper field boundary negation
        metrics["N - 8 Mirror Complement"] = (N - 8) - scalar_candidate
        
        # 3. Fractional Exponent Projections (height / 256)
        fractional_exponent = self.height / 256.0
        if self.target_x:
            metrics[f"X^({self.height}/256) Projection"] = float(pow(self.target_x, int(self.height), P))**fractional_exponent
        else:
            metrics[f"X^({self.height}/256) Projection"] = "N/A"
            
        if self.target_y:
            metrics[f"Y^({self.height}/256) Projection"] = float(pow(self.target_y, int(self.height), P))**fractional_exponent
        else:
            metrics[f"Y^({self.height}/256) Projection"] = "N/A"
            
        # 4. Calibration scoring if checking against a known solved key
        if self.solved_key:
            drift = abs(scalar_candidate - self.solved_key)
            metrics["Lattice Key Match?"] = "MATCH FOUND" if drift == 0 else "NO"
            metrics["Linear Key Distance"] = drift
            metrics["Log2 Key Drift Score"] = round(math.log2(drift), 4) if drift > 0 else "0.0 (Perfect Intercept)"
        else:
            metrics["Lattice Key Match?"] = "Unconfirmed Target"
            metrics["Linear Key Distance"] = "N/A"
            metrics["Log2 Key Drift Score"] = "N/A"
            
        return metrics

    def execute_plan(self):
        print(f"=== REVERSAL LAND TESTING MATRIX: PUZZLE HEIGHT {self.height} ===")
        print(f"Range Envelope: 2^{self.height-1} to 2^{self.height} - 1")
        print(f"Macro Delta Window (D): {self.D}")
        print(f"Midpoint Reference Line: {self.mid}")
        print("-" * 70)
        
        lanes = self.generate_lanes()
        results_matrix = []
        
        for name, scalar in lanes.items():
            results_matrix.append(self.evaluate_lane(name, scalar))
            
        # If calibration key is present, evaluate where the real private key sits relative to the lanes
        if self.solved_key:
            results_matrix.append(self.evaluate_lane("★ Ground Truth (Solved Key)", self.solved_key))
            
        return results_matrix

def print_table(matrix_data):
    """
    Formats the processed metrics cleanly into database cell tracking rows
    """
    for row in matrix_data:
        print(f"\n[Register Row]: {row['Lane Description']}")
        print(f" ├── Candidate Scalar: {row['Scalar Candidate (Hex)']}")
        print(f" ├── Log2 Height Rank: {row['Log2 Normalization']}")
        print(f" ├── Offset from Mid:  {row['Distance to Midpoint']}")
        print(f" ├── Complement (N-8): {row['N - 8 Mirror Complement']}")
        if "Log2 Key Drift Score" in row:
            print(f" └── Sieve Accuracy Score (Key Drift): {row['Log2 Key Drift Score']}")
        print("-" * 50)


# ==========================================
# EXECUTION DEPLOYMENT LAYER
# ==========================================
if __name__ == "__main__":
    
    # Run Calibration Phase 1: Known Solved Target Example (Puzzle 10)
    # Range: 2^9 to 2^10 - 1 (512 to 1023). Real Key Example: 714 (0x2CA)
    solved_puzzle_height = 10
    known_private_key = 714
    
    calibration_run = ReversalTestPlan(
        puzzle_height=solved_puzzle_height, 
        solved_priv_key=known_private_key
    )
    matrix_out_1 = calibration_run.execute_plan()
    print_table(matrix_out_1)
    
    print("\n" * 2)
    
    # Run Diagnostic Phase 2: Target Puzzle 135 Corridor Matrix Mapping
    # Range: 2^134 to 2^135 - 1
    # Coordinates derived from target block data anchors
    puzzle_135_x = 9210836494447108270027136741376870869791784014198948301625976867708124077590
    puzzle_135_y = 46351506704828816385393879789131775975171267756561783641521771795450741674800
    
    puzzle_135_run = ReversalTestPlan(
        puzzle_height=135,
        target_x=puzzle_135_x,
        target_y=puzzle_135_y
    )
    matrix_out_2 = puzzle_135_run.execute_plan()
    print_table(matrix_out_2)