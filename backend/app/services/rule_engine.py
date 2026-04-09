from typing import List, Dict, Any
from pydantic import BaseModel
from app.services.document_ai import ExtractedBill, BillItem
from app.services.policy_nlp import PolicyRule
from app.ontology.semantic_matcher import SemanticMatcher

class AdjudicationTrace(BaseModel):
    item_description: str
    original_amount: float
    ontology_category: str
    amount_covered: float
    amount_rejected: float
    rejection_reason: str
    rule_applied: str

class ClaimResult(BaseModel):
    total_billed: float
    total_covered: float
    total_rejected: float
    traces: List[AdjudicationTrace]

class RuleEngine:
    def __init__(self):
        self.matcher = SemanticMatcher(use_offline=True)

    def adjudicate(self, bill: ExtractedBill, rules: List[PolicyRule]) -> ClaimResult:
        traces = []
        total_covered = 0.0
        total_rejected = 0.0
        
        # Extract global copay rule if present
        global_copay = next((r.copay_percentage for r in rules if r.category == "All" and r.copay_percentage is not None), 0.0)

        for item in bill.items:
            amount_covered = 0.0
            amount_rejected = 0.0
            rejection_reason = "Approved"
            rule_applied = "Standard Coverage"
            
            # 1. Semantic matching
            match_data = self.matcher.match_item(item.description)
            category = match_data["category"]
            
            # 2. Check exclusions
            is_excluded = match_data.get("is_exclusion", False)
            for r in rules:
                if r.category == category and r.is_excluded:
                    is_excluded = True
                    rule_applied = r.raw_clause
            
            if is_excluded:
                amount_rejected = item.amount
                rejection_reason = "Item is strictly excluded by policy."
                if rule_applied == "Standard Coverage":
                     rule_applied = "Default Ontology Exclusion"
            else:
                # 3. Apply Caps
                cap = None
                for r in rules:
                    if r.category == category and r.cap_amount is not None:
                        cap = r.cap_amount
                        rule_applied = r.raw_clause
                
                amount_to_cover = item.amount
                if cap is not None and item.amount > cap:
                    amount_rejected = item.amount - cap
                    amount_to_cover = cap
                    rejection_reason = f"Exceeded category cap of Rs {cap}"
                
                # 4. Apply Co-pay
                if global_copay > 0:
                     copay_deduction = amount_to_cover * (global_copay / 100.0)
                     amount_to_cover -= copay_deduction
                     amount_rejected += copay_deduction
                     if "Exceeded" not in rejection_reason:
                         rejection_reason = f"{global_copay}% Co-pay applied."
                     else:
                         rejection_reason += f" and {global_copay}% Co-pay applied."
                
                amount_covered = amount_to_cover

            total_covered += amount_covered
            total_rejected += amount_rejected
            
            traces.append(AdjudicationTrace(
                item_description=item.description,
                original_amount=item.amount,
                ontology_category=category,
                amount_covered=amount_covered,
                amount_rejected=amount_rejected,
                rejection_reason=rejection_reason,
                rule_applied=rule_applied
            ))

        return ClaimResult(
            total_billed=bill.total_billed,
            total_covered=total_covered,
            total_rejected=total_rejected,
            traces=traces
        )
