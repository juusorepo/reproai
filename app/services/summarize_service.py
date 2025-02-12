"""
Summarize Service
---------------

This module provides functionality for generating summaries of compliance analysis results
using OpenAI's API.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
import json
import re
from collections import defaultdict
from app.models.manuscript import Manuscript
from app.models.compliance_result import ComplianceResult
from .llm_service import get_llm_response

class SummarizeService:
    """Service for generating summaries of compliance analysis results."""
    
    def __init__(self, api_key: str, db_service):
        """Initialize the summarize service.
        
        Args:
            api_key: OpenAI API key
            db_service: Database service instance
        """
        self.api_key = api_key
        self.db_service = db_service
        self._load_prompt_templates()
        
    def _load_prompt_templates(self):
        """Load the prompt templates from files."""
        prompts_dir = Path(__file__).parent.parent / "prompts"
        
        with open(prompts_dir / "summarize_overview.txt", 'r', encoding='utf-8') as f:
            self.overview_template = f.read()
            
        with open(prompts_dir / "summarize_categories.txt", 'r', encoding='utf-8') as f:
            self.categories_template = f.read()
            
    def _format_results_for_prompt(self, results: List[ComplianceResult], checklist_items: List[Dict]) -> Tuple[str, Dict[str, List[ComplianceResult]]]:
        """Format compliance results for the prompt.
        
        Args:
            results: List of compliance results
            checklist_items: List of checklist items with categories
            
        Returns:
            Tuple of (formatted string, category_results mapping)
        """
        # Create mapping of item_id to category
        item_categories = {item["item_id"]: item["category"] for item in checklist_items}
        
        # Group results by category
        category_results = defaultdict(list)
        for result in results:
            category = item_categories.get(result.item_id, "Other")
            category_results[category].append(result)
            
        # Format results by category
        formatted = []
        for category, cat_results in category_results.items():
            formatted.append(f"\nCategory: {category}")
            for result in cat_results:
                item = f"\nItem {result.item_id}:\n"
                item += f"Question: {result.question}\n"
                item += f"Compliance: {result.compliance}\n"
                item += f"Explanation: {result.explanation}\n"
                if result.quote:
                    item += f"Quote: {result.quote}\n"
                if result.section:
                    item += f"Section: {result.section}\n"
                formatted.append(item)
                
        return "\n".join(formatted), dict(category_results)
            
    def _clean_json_response(self, response: str) -> str:
        """Clean JSON response by removing markdown code block markers.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            Cleaned JSON string
        """
        # Remove markdown code block markers if present
        response = re.sub(r'^```json\s*', '', response)
        response = re.sub(r'\s*```$', '', response)
        return response.strip()
            
    def generate_summary(self, manuscript: Manuscript, results: List[ComplianceResult]) -> str:
        """Generate a summary of compliance results.
        
        Args:
            manuscript: Manuscript object containing metadata
            results: List of compliance results
            
        Returns:
            Generated summary text
        """
        # Get checklist items for categories
        checklist_items = self.db_service.get_checklist_items()
        all_categories = sorted(set(item["category"] for item in checklist_items))
        
        # Format manuscript info
        manuscript_info = (
            f"Title: {manuscript.title}\n"
            f"Authors: {', '.join(manuscript.authors)}\n"
            f"DOI: {manuscript.doi}\n"
        )
        
        # Format results and get category mapping
        formatted_results, category_results = self._format_results_for_prompt(results, checklist_items)
        
        # Get overview summary
        overview = get_llm_response(
            prompt=self.overview_template.format(
                manuscript=manuscript_info,
                results=formatted_results
            ),
            system_prompt="You are a scientific manuscript analyzer that summarizes compliance analysis results. Be concise and focus on key findings and actionable recommendations.",
            temperature=0.3,  # Slightly higher for more natural language
            max_tokens_output=1000  # Overview should be concise
        )
        
        # Get category-based summary
        categories_json = get_llm_response(
            prompt=self.categories_template.format(
                manuscript=manuscript_info,
                results=formatted_results,
                categories=", ".join(all_categories)  # Pass all categories to the prompt
            ),
            system_prompt="You are a scientific manuscript analyzer that categorizes compliance issues. Return only valid JSON without any other text.",
            temperature=0,  # Keep it deterministic for JSON
            max_tokens_output=1000
        )
        
        # Parse categories and prepare structured summary
        try:
            # Clean the JSON response
            categories_json = self._clean_json_response(categories_json)
            categories = json.loads(categories_json)
            
            # Prepare category summaries for database
            category_summaries = []
            for category in all_categories:
                if category in categories["categories"]:
                    details = categories["categories"][category]
                    category_summaries.append({
                        "category": category,
                        "summary": details["summary"],
                        "severity": details["severity"],
                        "original_results": [result.to_dict() for result in category_results.get(category, [])]
                    })
                else:
                    category_summaries.append({
                        "category": category,
                        "summary": "ok.",
                        "severity": "low",
                        "original_results": [result.to_dict() for result in category_results.get(category, [])]
                    })
            
            # Save structured summary to database
            self.db_service.save_summary(manuscript.doi, overview, category_summaries)
            
            # Format the display summary
            final_summary = overview + "\n\n### CATEGORY-BASED ISSUES:\n\n"
            for summary in category_summaries:
                final_summary += f"**{summary['category']}** (Severity: {summary['severity'].upper()}):\n"
                final_summary += f"- {summary['summary']}\n\n"
                
        except json.JSONDecodeError as e:
            print(f"Error parsing categories JSON: {str(e)}")
            print(f"Raw JSON response: {categories_json}")
            final_summary = overview + "\n\nError: Could not parse category-based issues."
        
        return final_summary
