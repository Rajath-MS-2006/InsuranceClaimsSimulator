import os
import re
from pydantic import BaseModel
from typing import List, Optional
from app.ontology.semantic_matcher import SemanticMatcher

class PolicyRule(BaseModel):
    category: str
    cap_amount: Optional[float] = None
    copay_percentage: Optional[float] = None
    is_excluded: bool = False
    raw_clause: str

class PolicyParser:
    def __init__(self, use_offline=True):
        self.matcher = SemanticMatcher(use_offline=use_offline)
        
    def parse_policy_text(self, policy_text: str) -> List[PolicyRule]:
        """
        Parses raw unstructured policy text into structured deterministic rules exactly matching
        the SemanticMatcher's categories, using lightweight Regex parsing.
        """
        rules = []
        
        sentences = re.split(r'(?<=[.!?]) +', policy_text.replace('\n', ' '))
        
        for original_text in sentences:
            if not original_text.strip():
                continue
            text = original_text.lower()
            
            # Analyze intent / exclusions
            is_exclusion = any(term in text for term in ["not covered", "exclude", "exclusion", "strictly excluded", "does not cover", "not included", "not payable"])
            
            # Look for copays (explicit mention of copay)
            is_copay = "copay" in text or "co-pay" in text
            
            # RegEx to find numbers (caps)
            money_vals = []
            matches = re.findall(r'(?:rs|inr|\$|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)', text)
            for m in matches:
                cleaned = m.replace(',', '')
                try:
                    if cleaned:
                        money_vals.append(float(cleaned))
                except ValueError:
                    pass
            
            if is_copay:
                copay_match = re.search(r'(\d+)%', text)
                if copay_match:
                    copay_val = float(copay_match.group(1))
                else:
                    copay_val = 10.0 # Default fallback
                
                rules.append(PolicyRule(category="All", copay_percentage=copay_val, raw_clause=original_text))
                continue
                
            # Remove filler words to improve matching
            stopwords = ["we", "they", "insurance", "policy", "it", "claims", "the", "a", "an", "is", "are"]
            words = [w for w in text.split() if w not in stopwords]
            subject_text = " ".join(words)
            
            # Classify using semantic matching
            match_data = self.matcher.match_item(subject_text, threshold=30)
            cat = match_data["category"]
            
            if is_exclusion:
                rules.append(PolicyRule(category=cat, is_excluded=True, raw_clause=original_text))
            elif money_vals and any(limit_word in text for limit_word in ["cap", "limit", "up to", "maximum", "max"]):
                cap = max(money_vals) # Assume largest number is cap
                rules.append(PolicyRule(category=cat, cap_amount=cap, raw_clause=original_text))

        return rules

if __name__ == "__main__":
    parser = PolicyParser()
    sample_text = "Hospitalization room rent is capped at Rs 5000 per day. Cosmetic surgery is not covered. There is a 10% co-pay on all approved claims. Consumables are strictly excluded."
    rules = parser.parse_policy_text(sample_text)
    for r in rules:
        print(r)
