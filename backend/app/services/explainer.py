from typing import List
from app.services.rule_engine import ClaimResult

class Explainer:
    @staticmethod
    def generate_report(result: ClaimResult) -> str:
        """
        Generates a human-readable and research-verifiable explanation of the claim adjudication.
        """
        lines = []
        lines.append("=== Claim Adjudication Explanation ===")
        lines.append(f"Total Billed: Rs {result.total_billed}")
        lines.append(f"Total Covered: Rs {result.total_covered}")
        lines.append(f"Patient Payable (Rejected/Copay): Rs {result.total_rejected}")
        lines.append("--------------------------------------")
        lines.append("Itemized Breakdown:")
        
        for idx, trace in enumerate(result.traces):
            lines.append(f"{idx+1}. {trace.item_description} (Rs {trace.original_amount}) -> Category: {trace.ontology_category}")
            
            if trace.amount_rejected > 0:
                lines.append(f"   [REJECTED Rs {trace.amount_rejected}] Reason: {trace.rejection_reason}")
                lines.append(f"   [RULE APPLIED]: \"{trace.rule_applied}\"")
            
            lines.append(f"   [COVERED Rs {trace.amount_covered}]")
            lines.append("")
            
        return "\n".join(lines)
