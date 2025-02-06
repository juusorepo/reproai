import os
from typing import Dict, Any, List
from datetime import datetime
import openai
from ..models.manuscript import Manuscript
from ..models.compliance_result import ComplianceResult
from ..services.db_service import DatabaseService

class ComplianceAnalyzer:
    def __init__(self, api_key: str, db_service: DatabaseService):
        """Initialize the compliance analyzer."""
        self.api_key = api_key
        self.db_service = db_service
        openai.api_key = api_key

    def validate_compliance_result(self, response_text: str) -> Dict[str, Any]:
        """
        Validate and clean the JSON response from GPT.
        
        Args:
            response_text: Raw response from GPT
            
        Returns:
            Cleaned and validated JSON dictionary
        """
        try:
            # Try to find JSON-like content between curly braces
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON object found in response")
            
            json_str = json_match.group(0)
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["compliance", "explanation", "quote", "section"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Validate compliance value
            valid_compliance = ["Yes", "No", "Partial", "n/a"]
            if data["compliance"] not in valid_compliance:
                raise ValueError(f"Invalid compliance value: {data['compliance']}")
            
            return {
                "compliance": str(data["compliance"]).strip(),
                "explanation": str(data["explanation"]).strip(),
                "quote": str(data["quote"]).strip(),
                "section": str(data["section"]).strip()
            }
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing response: {str(e)}")

    def analyze_item(self, manuscript: Manuscript, text: str, checklist_item: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single checklist item for compliance."""
        print(f"Analyzing item {checklist_item['item_id']}: {checklist_item['question']}")
        
        # Prepare the prompt for GPT
        prompt = f"""
        You are analyzing a scientific manuscript for compliance with reporting guidelines.
        
        MANUSCRIPT TEXT (first 15000 chars):
        {text[:15000]}
        
        CHECKLIST ITEM:
        {checklist_item['question']}
        
        TASK:
        1. Determine if the manuscript complies with this checklist item.
        2. Find relevant quotes from the text that support your decision.
        3. Identify which section(s) of the paper contain the relevant information.
        
        OUTPUT FORMAT:
        Return a JSON object with these fields:
        - compliance: "Yes", "No", "Partial", or "n/a"
        - explanation: Brief explanation of your decision
        - quote: Most relevant quote from the text (or empty if none found)
        - section: Section where the quote was found (or empty if none found)
        """
        
        # Call GPT-4 for analysis
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a scientific manuscript analyzer that evaluates compliance with reporting guidelines. You output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=500
            )
            
            # Parse the response
            result = eval(response.choices[0].message.content)
            
            # Add metadata
            result.update({
                "item_id": checklist_item["item_id"],
                "question": checklist_item["question"],
                "created_at": datetime.now()
            })
            
            return result
            
        except Exception as e:
            print(f"Error analyzing item {checklist_item['item_id']}: {str(e)}")
            return {
                "item_id": checklist_item["item_id"],
                "question": checklist_item["question"],
                "compliance": "n/a",
                "explanation": f"Error during analysis: {str(e)}",
                "quote": "",
                "section": "",
                "created_at": datetime.now()
            }

    def analyze_compliance(self, text: str, doi: str, save_to_db: bool = True, debug: bool = False) -> List[Dict[str, Any]]:
        """Analyze manuscript compliance with all checklist items."""
        # Get all checklist items
        checklist_items = self.db_service.get_checklist_items()
        print(f"Found {len(checklist_items)} checklist items to analyze")
        
        # Create a dummy manuscript object
        manuscript = Manuscript(
            doi=doi,
            title="",
            authors=[],
            abstract="",
            design="",
            pdf_path=""
        )
        
        # Analyze each item
        results = []
        for item in checklist_items:
            result = self.analyze_item(manuscript, text, item)
            results.append(result)
            
            # Save to database if requested
            if save_to_db:
                self.db_service.save_compliance_result(doi, result)
                
            if debug:
                print(f"\nAnalyzed item {item['item_id']}:")
                print(f"Compliance: {result['compliance']}")
                print(f"Explanation: {result['explanation']}")
                if result['quote']:
                    print(f"Quote: {result['quote']}")
                if result['section']:
                    print(f"Section: {result['section']}")
                    
        return results
