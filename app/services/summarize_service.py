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
            
    def _format_results_for_prompt(self, results: List[Dict[str, Any]], checklist_items: List[Dict]) -> Tuple[str, Dict[str, List[Dict[str, Any]]]]:
        """Format compliance results for the prompt.
        
        Args:
            results: List of compliance results
            checklist_items: List of checklist items with categories
            
        Returns:
            Tuple containing:
            - Formatted results string for overview
            - Dictionary mapping categories to their results
        """
        # Create item_id to category mapping
        item_categories = {item['item_id']: item['category'] for item in checklist_items}
        
        # Group results by category
        results_by_category = defaultdict(list)
        formatted_results = []
        
        for result in results:
            item_id = result['item_id']
            category = item_categories.get(item_id, 'Uncategorized')
            results_by_category[category].append(result)
            
            formatted_result = (
                f"Item {item_id}:\n"
                f"Question: {result['question']}\n"
                f"Compliance: {result['compliance']}\n"
                f"Explanation: {result['explanation']}\n"
                f"Supporting Quotes: {result.get('quote', 'None')}\n"
                f"Manuscript DOI: {result.get('doi', 'No DOI')}\n"
            )
            formatted_results.append(formatted_result)
            
        return "\n".join(formatted_results), dict(results_by_category)

    def summarize_results(self, results: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
        """Generate summary of compliance analysis results.
        
        Args:
            results: List of compliance results
            
        Returns:
            Tuple containing:
            - Overview summary
            - List of category summaries, each containing:
              - category: Category name
              - summary: Category-specific summary
              - severity: Severity level (low, medium, high)
              - original_results: List of original compliance results for the category
        """
        try:
            # Get checklist items for categories
            checklist_items = self.db_service.get_checklist_items()
            if not checklist_items:
                print("Error: No checklist items found")
                return "", []

            # Format results and get category mapping
            formatted_results, results_by_category = self._format_results_for_prompt(results, checklist_items)
            
            if not formatted_results or not results_by_category:
                print("Error: Could not format results")
                return "", []

            # Generate overview summary
            overview_prompt = self.overview_template.format(
                results=formatted_results,
                manuscript_doi=results[0].get('doi', 'No DOI') if results else 'No DOI'
            )
            overview = get_llm_response(
                prompt=overview_prompt,
                system_prompt="You are a scientific manuscript analyzer that summarizes compliance analysis results.",
                temperature=0.3,
                response_format={"type": "text"}
            )
            
            # Format all categories for a single API call
            all_categories_results = []
            categories = []
            for category, category_results in results_by_category.items():
                categories.append(category)
                formatted_results = "\n".join([
                    f"Category: {category}\n"
                    f"Item {r['item_id']}:\n"
                    f"Question: {r['question']}\n"
                    f"Compliance: {r['compliance']}\n"
                    f"Explanation: {r['explanation']}\n"
                    f"Supporting Quotes: {r.get('quote', 'None')}\n"
                    f"Manuscript DOI: {r.get('doi', 'No DOI')}\n"
                    for r in category_results
                ])
                all_categories_results.append(formatted_results)
            
            # Generate all category summaries in one call
            categories_prompt = self.categories_template.format(
                categories=", ".join(categories),
                results="\n\n".join(all_categories_results),
                manuscript_doi=results[0].get('doi', 'No DOI') if results else 'No DOI'
            )
            
            # Get JSON response for all categories
            json_response = get_llm_response(
                prompt=categories_prompt,
                system_prompt="You are a scientific manuscript analyzer that summarizes compliance analysis results for specific categories. Return only valid JSON.",
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parse JSON response
            try:
                cleaned_json = json_response.strip()
                if not cleaned_json.startswith('{'):
                    print("Error: Invalid JSON response format")
                    raise json.JSONDecodeError("Invalid JSON", json_response, 0)
                
                categories_data = json.loads(cleaned_json)
                
                if not isinstance(categories_data, dict) or 'categories' not in categories_data:
                    print("Error: Invalid JSON structure")
                    raise ValueError("Invalid JSON structure")
                
                category_summaries = []
                for category, data in categories_data['categories'].items():
                    if not isinstance(data, dict):
                        print(f"Warning: Invalid data format for category {category}")
                        continue
                        
                    category_summaries.append({
                        'category': category,
                        'summary': data.get('summary', ''),
                        'severity': data.get('severity', 'low'),
                        'original_results': results_by_category.get(category, [])
                    })
                
                severity_order = {'high': 0, 'medium': 1, 'low': 2}
                category_summaries.sort(key=lambda x: severity_order.get(x['severity'].lower(), 3))
                
                return overview, category_summaries
                    
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error parsing JSON: {str(e)}")
                category_summaries = []
                for category, category_results in results_by_category.items():
                    severity = 'high' if any(r.get('compliance') == 'No' for r in category_results) \
                             else 'medium' if any(r.get('compliance') == 'Partial' for r in category_results) \
                             else 'low'
                    category_summaries.append({
                        'category': category,
                        'summary': f"Error generating summary for {category}",
                        'severity': severity,
                        'original_results': category_results
                    })
                return overview, category_summaries
                
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return "", []

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
        formatted_results, category_results = self._format_results_for_prompt([result.to_dict() for result in results], checklist_items)
        
        # Get overview summary
        overview = get_llm_response(
            prompt=self.overview_template.format(
                manuscript=manuscript_info,
                results=formatted_results
            ),
            system_prompt="You are a scientific manuscript analyzer that summarizes compliance analysis results. Be concise and focus on key findings and actionable recommendations.",
            temperature=0.3,  # Slightly higher for more natural language
            max_tokens_output=1000,  # Overview should be concise
            response_format={"type": "text"}
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
            categories_json = self._clean_json_response(categories_json)
            categories = json.loads(categories_json)
            
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
                        "original_results": []
                    })
            
            self.db_service.save_summary(manuscript.doi, overview, category_summaries)
            
            final_summary = overview + "\n\n### CATEGORY-BASED ISSUES:\n\n"
            for summary in category_summaries:
                final_summary += f"**{summary['category']}** (Severity: {summary['severity'].upper()}):\n"
                final_summary += f"- {summary['summary']}\n\n"
                
        except json.JSONDecodeError as e:
            print(f"Error parsing categories JSON: {str(e)}")
            print(f"Raw JSON response: {categories_json}")
            final_summary = overview + "\n\nError: Could not parse category-based issues."
        
        return final_summary

    def _clean_json_response(self, response: str) -> str:
        """Clean JSON response by removing markdown code block markers.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            Cleaned JSON string
        """
        response = re.sub(r'^```(?:json)?\s*', '', response)
        response = re.sub(r'\s*```$', '', response)
        
        response = response.strip()
        first_brace = response.find('{')
        last_brace = response.rfind('}')
        if first_brace != -1 and last_brace != -1:
            response = response[first_brace:last_brace + 1]
            
        return response.strip()
