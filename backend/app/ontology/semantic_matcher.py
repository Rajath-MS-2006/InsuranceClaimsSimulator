import os
import json
from thefuzz import process

class SemanticMatcher:
    def __init__(self, use_offline=True):
        self.ontology = self._load_ontology()
        self._build_embeddings()

    def _load_ontology(self):
        ontology_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'data', 'ontology_base.json')
        try:
            with open(ontology_path, 'r') as f:
                data = json.load(f)
                return data['categories']
        except Exception as e:
            print(f"Failed to load ontology: {e}")
            return []

    def _build_embeddings(self):
        self.categories_data = []
        self.term_list = []
        
        for category in self.ontology:
            cat_name = category['name']
            aliases = category.get('aliases', [])
            all_terms = [cat_name] + aliases
            
            for term in all_terms:
                self.term_list.append(term)
                self.categories_data.append({
                    "term": term,
                    "category": cat_name,
                    "is_exclusion": category.get('default_exclusion', False)
                })

    def match_item(self, item_description: str, threshold=40):
        """
        Given a line item from a hospital bill (e.g. 'Crocin Advance 500mg'),
        find the closest matching category in the ontology using fuzzy matching.
        """
        if not self.term_list:
             return {
                "category": "Miscellaneous",
                "matched_term": None,
                "confidence": 0,
                "is_exclusion": True
            }

        best_match_str, best_score = process.extractOne(item_description, self.term_list)
        
        if best_score >= threshold:
            best_match_data = next((item for item in self.categories_data if item["term"] == best_match_str), None)
            return {
                "category": best_match_data["category"] if best_match_data else "Miscellaneous",
                "matched_term": best_match_str,
                "confidence": best_score / 100.0,
                "is_exclusion": best_match_data["is_exclusion"] if best_match_data else True
            }
        else:
            return {
                "category": "Miscellaneous",
                "matched_term": None,
                "confidence": best_score / 100.0,
                "is_exclusion": True
            }

if __name__ == "__main__":
    matcher = SemanticMatcher()
    print(matcher.match_item("MRI Scan of Head"))
    print(matcher.match_item("Antibiotic IV Injection"))
    print(matcher.match_item("Private AC Room"))
