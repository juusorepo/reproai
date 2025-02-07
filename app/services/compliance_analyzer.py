"""
Compliance Analyzer Service
-------------------------

This module provides the ComplianceAnalyzer class which is responsible for analyzing
manuscripts for reproducibility compliance. It uses OpenAI's API to analyze the text
and determine compliance with various reproducibility criteria.

The analyzer:
1. Breaks down the manuscript into sections
2. Analyzes each section against predefined compliance criteria
3. Generates detailed explanations and extracts relevant quotes
4. Stores the results in the database
"""

import os
from typing import Dict, Any, List
from datetime import datetime
import openai
import re
import json
import time
from ..models.manuscript import Manuscript
from ..models.compliance_result import ComplianceResult
from ..services.db_service import DatabaseService

class ComplianceAnalyzer:
    """A class for analyzing manuscript reproducibility compliance.
    
    This class uses OpenAI's API to analyze manuscripts against a set of
    reproducibility criteria. For each criterion, it determines compliance
    level, provides explanations, and extracts supporting quotes.
    
    Attributes:
        api_key (str): OpenAI API key
        db_service (DatabaseService): Database service for storing results
    """
    
    # GPT-4 Turbo has a 128k token limit, using ~100k for text to leave room for prompt and response
    MAX_CONTEXT_LENGTH = 400000  # ~100k tokens assuming 4 chars per token

    def __init__(self, api_key: str, db_service: DatabaseService):
        """Initialize the ComplianceAnalyzer.
        
        Args:
            api_key: OpenAI API key
            db_service: Database service instance
        """
        self.api_key = api_key
        self.db_service = db_service
        openai.api_key = api_key

    def fit_to_context(self, text: str) -> str:
        """Take the last N characters that fit in the context window."""
        if len(text) <= self.MAX_CONTEXT_LENGTH:
            return text
        print(f"Text length ({len(text)}) exceeds context window, truncating to {self.MAX_CONTEXT_LENGTH} characters")
        return text[-self.MAX_CONTEXT_LENGTH:]

    def analyze_item(self, manuscript: Manuscript, text: str, checklist_item: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single checklist item for compliance.
        
        Uses OpenAI to:
        1. Determine if the manuscript complies with the item
        2. Generate an explanation for the compliance level
        3. Extract relevant quotes from the text
        4. Identify which section contains the evidence
        
        Args:
            manuscript: The manuscript to analyze
            text: The text to analyze
            item: The checklist item to analyze
            
        Returns:
            Dictionary containing the analysis results
        """
        print(f"Analyzing item {checklist_item['item_id']}: {checklist_item['question']}")
        
        try:
            # Fit text to context window
            text = self.fit_to_context(text)
            print(f"Text length after fitting to context: {len(text)} characters")
            
            # Prepare the prompt for GPT
            prompt = f"""
            You are analyzing a scientific manuscript for compliance with reporting guidelines.
            
            MANUSCRIPT TEXT:
            {text}
            
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
            
            # Call GPT-4 Turbo for analysis
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4-0125-preview",  # GPT-4 Turbo with 128k context window
                    messages=[
                        {"role": "system", "content": "You are a scientific manuscript analyzer that evaluates compliance with reporting guidelines. You output only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0,
                    max_tokens=1000  # Increased for more detailed responses
                )
                
                # Parse the response
                response_text = response.choices[0].message.content
                try:
                    # Clean the response text from markdown code block markers
                    clean_text = response_text.strip()
                    if clean_text.startswith('```json'):
                        clean_text = clean_text[7:]  # Remove ```json prefix
                    if clean_text.endswith('```'):
                        clean_text = clean_text[:-3]  # Remove ``` suffix
                    clean_text = clean_text.strip()
                    result = json.loads(clean_text)
                except json.JSONDecodeError:
                    print(f"Error parsing JSON response for item {checklist_item['item_id']}")
                    print(f"Raw response: {response_text}")
                    raise
                
                # Validate compliance value
                valid_compliance = ["Yes", "No", "Partial", "n/a"]
                if result.get("compliance") not in valid_compliance:
                    print(f"Invalid compliance value received: {result.get('compliance')}")
                    result["compliance"] = "n/a"
                    result["explanation"] = "Error: Invalid compliance value received"
                
                # Add metadata
                result.update({
                    "item_id": checklist_item["item_id"],
                    "question": checklist_item["question"],
                    "created_at": datetime.now(),
                    "doi": manuscript.doi
                })
                
                print(f"Successfully analyzed item {checklist_item['item_id']}: {result['compliance']}")
                
                # Add small delay between API calls to avoid rate limits
                time.sleep(1)
                
                return result
                
            except openai.error.RateLimitError as e:
                print(f"Rate limit error: {str(e)}")
                raise
                
        except Exception as e:
            error_result = {
                "item_id": checklist_item["item_id"],
                "question": checklist_item["question"],
                "compliance": "n/a",
                "explanation": f"Error during analysis: {str(e)}",
                "quote": "",
                "section": "",
                "created_at": datetime.now(),
                "doi": manuscript.doi
            }
            print(f"Error analyzing item {checklist_item['item_id']}: {str(e)}")
            return error_result

    def analyze_compliance(self, text: str, doi: str, save_to_db: bool = True, debug: bool = False) -> List[Dict[str, Any]]:
        """Analyze manuscript compliance with all checklist items.
        
        This method:
        1. Gets the checklist items from the database
        2. Analyzes each item using OpenAI
        3. Stores the results in the database
        4. Updates the manuscript's analysis date
        
        Args:
            text: The text to analyze
            doi: The DOI of the manuscript
            save_to_db: Whether to save the results to the database
            debug: Whether to print debug information
            
        Returns:
            List of compliance results
        """
        print(f"\nStarting compliance analysis for manuscript with DOI: {doi}")
        print(f"Text length: {len(text)} characters")
        
        # Get all checklist items
        checklist_items = self.db_service.get_checklist_items()
        print(f"Found {len(checklist_items)} checklist items to analyze")
        
        # Create a manuscript object
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
        successful_analyses = 0
        failed_analyses = 0
        
        for item in checklist_items:
            try:
                result = self.analyze_item(manuscript, text, item)
                results.append(result)
                
                # Save to database if requested
                if save_to_db:
                    try:
                        self.db_service.save_compliance_result(doi, result)
                        print(f"Saved result for item {item['item_id']} to database")
                        successful_analyses += 1
                    except Exception as e:
                        print(f"Error saving result for item {item['item_id']} to database: {str(e)}")
                        failed_analyses += 1
                
                if debug:
                    print(f"\nAnalyzed item {item['item_id']}:")
                    print(f"Compliance: {result['compliance']}")
                    print(f"Explanation: {result['explanation']}")
                    if result['quote']:
                        print(f"Quote: {result['quote']}")
                    if result['section']:
                        print(f"Section: {result['section']}")
            except Exception as e:
                print(f"Error processing item {item['item_id']}: {str(e)}")
                failed_analyses += 1
                continue
        
        print(f"\nAnalysis complete:")
        print(f"- Successful analyses: {successful_analyses}")
        print(f"- Failed analyses: {failed_analyses}")
        print(f"- Total items processed: {len(results)}")
                    
        return results
