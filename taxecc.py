import math

class CryptoTaxPipeline:
    def __init__(self, raw_transactions: list, partner_share: float = 1.0):
        """
        :param raw_transactions: List of dicts containing 'type', 'fiat_value', and 'gas_fee_fiat'
        :param partner_share: Float between 0.0 and 1.0 representing ownership share (Schedule K-1)
        """
        self.transactions = raw_transactions
        self.partner_share = partner_share
        
        # Pipeline Data Nodes
        self.schedule_c = {"gross_receipts": 0.0, "total_expenses": 0.0, "net_profit": 0.0}
        self.schedule_k1 = {"distributed_profit": 0.0}
        self.schedule_se = {"taxable_earnings": 0.0, "se_tax_owed": 0.0, "se_deduction": 0.0}
        self.schedule_1 = {"additional_income": 0.0, "above_the_line_deductions": 0.0}
        self.schedule_2 = {"other_taxes": 0.0}
        self.form_1040 = {"agi_impact": 0.0, "total_tax_impact": 0.0}

    def execute_pipeline(self):
        # 1. PROCESS SCHEDULE C (The Ingestion Node)
        for tx in self.transactions:
            if tx['type'] == 'revenue':
                self.schedule_c['gross_receipts'] += tx['fiat_value']
            # Gas/miner fees are deducted as ordinary business expenses
            self.schedule_c['total_expenses'] += tx['gas_fee_fiat']
            
        self.schedule_c['net_profit'] = max(0.0, self.schedule_c['gross_receipts'] - self.schedule_c['total_expenses'])
        
        # 2. PROCESS SCHEDULE K-1 (The Fractional Vector Splitter)
        # If part of a multi-sig partnership, split the net profit based on ownership share
        self.schedule_k1['distributed_profit'] = self.schedule_c['net_profit'] * self.partner_share
        
        # 3. PROCESS SCHEDULE SE (The Parallel Feedback Loop)
        # Rule: Multiply net earnings by 92.35% to find the taxable base
        self.schedule_se['taxable_earnings'] = self.schedule_k1['distributed_profit'] * 0.9235
        
        # Rule: Apply 15.3% Self-Employment Tax rate (12.4% Social Security up to cap + 2.9% Medicare)
        # For simplicity in this script, we assume income is under the Social Security wage cap
        self.schedule_se['se_tax_owed'] = self.schedule_se['taxable_earnings'] * 0.153
        
        # Rule: Half of the SE Tax is allowed as an above-the-line deduction
        self.schedule_se['se_deduction'] = self.schedule_se['se_tax_owed'] / 2.0
        
        # 4. PROCESS SCHEDULE 1 & SCHEDULE 2 (The Aggregators)
        self.schedule_1['additional_income'] = self.schedule_k1['distributed_profit']
        self.schedule_1['above_the_line_deductions'] = self.schedule_se['se_deduction']
        self.schedule_2['other_taxes'] = self.schedule_se['se_tax_owed']
        
        # 5. FINAL FORM 1040 INTEGRATION
        # Net impact to Adjusted Gross Income (AGI)
        self.form_1040['agi_impact'] = self.schedule_1['additional_income'] - self.schedule_1['above_the_line_deductions']
        # Absolute flat tax liability added to the return before standard bracket calculations
        self.form_1040['total_tax_impact'] = self.schedule_2['other_taxes']

    def print_tax_audit(self):
        print("=== CRYPTO-TO-TAX PIPELINE REPORT ===")
        print(f"Schedule C Net Profit:       ${self.schedule_c['net_profit']:.2f}")
        print(f"Schedule K-1 Split Profit:   ${self.schedule_k1['distributed_profit']:.2f} (Share: {self.partner_share * 100}%)")
        print("-" * 37)
        print(f"Schedule SE Taxable Base:    ${self.schedule_se['taxable_earnings']:.2f}")
        print(f"Schedule SE Total Tax Owed:  ${self.schedule_se['se_tax_owed']:.2f}")
        print("-" * 37)
        print(f"Schedule 1 Income Addition:  +${self.schedule_1['additional_income']:.2f}")
        print(f"Schedule 1 SE Deduction:     -${self.schedule_1['above_the_line_deductions']:.2f}")
        print(f"Schedule 2 Other Taxes:      +${self.schedule_2['other_taxes']:.2f}")
        print("=" * 37)
        print(f"NET FORM 1040 AGI INCREASE:  ${self.form_1040['agi_impact']:.2f}")
        print(f"FLAT SE TAX ADDED TO 1040:   ${self.form_1040['total_tax_impact']:.2f}")


# ====================================================================================================
# SIMULATION RUN: Processing secp256k1 on-chain business ledger
# ====================================================================================================
blockchain_ledger = [
    {"type": "revenue", "fiat_value": 50000.00, "gas_fee_fiat": 150.00},  # Client Payment A
    {"type": "revenue", "fiat_value": 35000.00, "gas_fee_fiat": 95.00},   # Client Payment B
    {"type": "expense", "fiat_value": 0.00,     "gas_fee_fiat": 500.00},  # Smart contract deploy
]

# Run pipeline as a 50/50 multi-sig business partner
pipeline = CryptoTaxPipeline(raw_transactions=blockchain_ledger, partner_share=0.5)
pipeline.execute_pipeline()
pipeline.print_tax_audit()