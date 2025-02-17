"""
Compliance Analyzer Service
-------------------------

This module provides functionality for analyzing manuscript compliance
with reproducibility guidelines using OpenAI's API.
"""

import os
from typing import Dict, Any, List
from datetime import datetime
import re
import json
import time
from ..models.manuscript import Manuscript
from ..models.compliance_result import ComplianceResult
from ..services.db_service import DatabaseService
from .llm_service import get_llm_response, truncate_to_token_limit, MAX_TOKENS_INPUT

class ComplianceAnalyzer:
    """A class for analyzing manuscript reproducibility compliance.
    
    This class uses OpenAI's API to analyze manuscripts against a set of
    reproducibility criteria. For each criterion, it determines compliance
    level, provides explanations, and extracts supporting quotes.
    
    Attributes:
        api_key (str): OpenAI API key
        db_service (DatabaseService): Database service for storing results
    """

    def __init__(self, api_key: str, db_service: DatabaseService):
        """Initialize the ComplianceAnalyzer.
        
        Args:
            api_key: OpenAI API key
            db_service: Database service instance
        """
        self.api_key = api_key
        self.db_service = db_service
        self._load_prompt_template()

    def _load_prompt_template(self):
        """Load the prompt template from file."""
        prompt_path = os.path.join('app', 'prompts', 'compliance_analysis.txt')
        with open(prompt_path, 'r') as f:
            self.prompt_template = f.read()

    def analyze_item(self, manuscript: Manuscript, text: str, checklist_item: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single checklist item for compliance.
        
        Args:
            manuscript: Manuscript object containing metadata
            text: Text content to analyze
            checklist_item: Dictionary containing item details
            
        Returns:
            Dictionary containing compliance analysis results
        """
        # Truncate text to fit within token limit if needed
        text_to_analyze = truncate_to_token_limit(text, MAX_TOKENS_INPUT)
        
        # Format prompt with item details and text
        prompt = self.prompt_template.format(
            item=checklist_item,
            text=text_to_analyze
        )
            
        # Call GPT-4 Turbo for analysis
        try:
            # Get response from LLM service
            response_text = get_llm_response(
                prompt=prompt,
                system_prompt="You are a scientific manuscript analyzer that evaluates compliance with reporting guidelines. You output only valid JSON.",
                temperature=0,
                max_tokens_output=2000  # Compliance analysis response should be relatively short
            )
            
            # Parse response
            result = json.loads(response_text)
            
            # Add metadata
            result["item_id"] = checklist_item["item_id"]
            result["question"] = checklist_item["question"]
            result["created_at"] = datetime.now()
            result["doi"] = manuscript.doi
            
            # Add small delay between API calls to avoid rate limits
            time.sleep(1)
            
            return result
            
        except Exception as e:
            print(f"Error during OpenAI API call: {str(e)}")
            raise

    def analyze_manuscript(self, manuscript: Manuscript, text: str, checklist_items: List[Dict[str, Any]], store_results: bool = True) -> List[Dict[str, Any]]:
        """Analyze a manuscript for compliance with all checklist items.
        
        Args:
            manuscript: Manuscript object containing metadata
            text: Text content to analyze
            checklist_items: List of dictionaries containing checklist item details
            store_results: Whether to store results in database
            
        Returns:
            List of dictionaries containing compliance analysis results
        """
        results = []
        errors = []
        
        for item in checklist_items:
            try:
                result = self.analyze_item(manuscript, text, item)
                results.append(result)
                
                # Save to database if requested
                if store_results:
                    self.db_service.compliance_results.update_one(
                        {
                            "doi": manuscript.doi,
                            "item_id": item["item_id"]
                        },
                        {"$set": result},
                        upsert=True
                    )
                    
            except Exception as e:
                error_msg = f"Error analyzing item {item['item_id']}: {str(e)}"
                print(error_msg)
                errors.append(error_msg)
                # Don't continue silently, try to reanalyze with a delay
                try:
                    print(f"Retrying analysis for item {item['item_id']} after delay...")
                    time.sleep(5)  # Wait 5 seconds before retry
                    result = self.analyze_item(manuscript, text, item)
                    results.append(result)
                    
                    if store_results:
                        self.db_service.compliance_results.update_one(
                            {
                                "doi": manuscript.doi,
                                "item_id": item["item_id"]
                            },
                            {"$set": result},
                            upsert=True
                        )
                except Exception as retry_e:
                    error_msg = f"Failed retry for item {item['item_id']}: {str(retry_e)}"
                    print(error_msg)
                    errors.append(error_msg)
                    continue
                
        if errors:
            print("Analysis completed with errors:")
            for error in errors:
                print(f"- {error}")
            
        if not results:
            raise Exception("No results were generated. Analysis failed completely.")
                
        return results
