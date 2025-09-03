"""Date-based filtering agent for GST filing periods."""

import google.generativeai as genai
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import json
import re
from datetime import datetime, date, timedelta
import calendar

load_dotenv()

class DateFilteringAgent:
    """Agent for filtering document chunks based on filing period dates."""
    
    def __init__(self):
        """Initialize the date filtering agent."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def filter_chunks_by_period(self, chunks: List[str], filing_month: str = None, filing_year: str = None, 
                               start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        Filter document chunks to only include transactions from the specified period.
        
        Args:
            chunks: List of document text chunks
            filing_month: Month name (e.g., "January", "February") - for monthly filing
            filing_year: Year as string (e.g., "2024") - for monthly filing
            start_date: Start date in DD/MM/YYYY format - for custom date range
            end_date: End date in DD/MM/YYYY format - for custom date range
            
        Returns:
            Dictionary containing filtered chunks and analysis
        """
        # Parse dates based on format
        if start_date and end_date:
            try:
                # Try YYYY-MM-DD format first (ISO format)
                if '-' in start_date:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                # Try DD/MM/YYYY format
                elif '/' in start_date:
                    start_dt = datetime.strptime(start_date, "%d/%m/%Y")
                    end_dt = datetime.strptime(end_date, "%d/%m/%Y")
                else:
                    return {"error": "Invalid date format. Use YYYY-MM-DD or DD/MM/YYYY format"}
            except ValueError as e:
                return {"error": f"Invalid date format. Use YYYY-MM-DD or DD/MM/YYYY format: {str(e)}"}
        elif filing_month and filing_year:
            # Monthly filing mode
            month_num = self._month_name_to_number(filing_month)
            if not month_num:
                return {"error": f"Invalid month: {filing_month}"}
            date_patterns = self._generate_date_patterns(month_num, filing_year)
            period_desc = f"{filing_month} {filing_year}"
        else:
            return {"error": "Either provide filing_month + filing_year OR start_date + end_date"}
        
        # Step 1: Quick keyword-based date filtering
        relevant_chunks = []
        
        for i, chunk in enumerate(chunks):
            if self._has_relevant_dates(chunk, date_patterns):
                relevant_chunks.append((i, chunk))
        
        # Step 2: AI-based date extraction for ambiguous cases
        if relevant_chunks:
            if start_date and end_date:
                ai_filtered = self._ai_date_range_filtering(relevant_chunks, start_date, end_date)
            else:
                ai_filtered = self._ai_date_filtering(relevant_chunks, filing_month, filing_year)
            return ai_filtered
        else:
            return {
                "filtered_chunks": [],
                "filing_period": period_desc,
                "total_original_chunks": len(chunks),
                "total_filtered_chunks": 0,
                "notes": f"No transactions found for {period_desc}"
            }
    
    def _month_name_to_number(self, month_name: str) -> Optional[int]:
        """Convert month name to number."""
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        return months.get(month_name.lower())
    
    def _generate_date_patterns(self, month_num: int, year: str) -> List[str]:
        """Generate various date patterns for the filing period."""
        month_abbr = calendar.month_abbr[month_num].lower()
        month_name = calendar.month_name[month_num].lower()
        
        patterns = [
            f"{month_num:02d}/{year}",  # 01/2024
            f"{month_num}/{year}",      # 1/2024
            f"{year}-{month_num:02d}",  # 2024-01
            f"{month_abbr} {year}",     # jan 2024
            f"{month_name} {year}",     # january 2024
            f"{month_abbr}.{year}",     # jan.2024
            f"{month_num:02d}.{year}",  # 01.2024
        ]
        
        # Add day-specific patterns for the month
        days_in_month = calendar.monthrange(int(year), month_num)[1]
        for day in range(1, min(days_in_month + 1, 32)):  # Limit to avoid too many patterns
            patterns.extend([
                f"{day:02d}/{month_num:02d}/{year}",     # 15/01/2024
                f"{day}/{month_num}/{year}",             # 15/1/2024
                f"{year}-{month_num:02d}-{day:02d}",     # 2024-01-15
                f"{day:02d}.{month_num:02d}.{year}",     # 15.01.2024
            ])
        
        return patterns
    
    def _generate_date_range_patterns(self, start_dt: datetime, end_dt: datetime) -> List[str]:
        """Generate date patterns for a custom date range."""
        patterns = []
        
        # Add specific date patterns for the range
        current_dt = start_dt
        while current_dt <= end_dt:
            # Various date formats for each day in range
            patterns.extend([
                current_dt.strftime("%d/%m/%Y"),     # 15/01/2024
                current_dt.strftime("%d-%m-%Y"),     # 15-01-2024
                current_dt.strftime("%d.%m.%Y"),     # 15.01.2024
                current_dt.strftime("%Y-%m-%d"),     # 2024-01-15
                current_dt.strftime("%d/%m/%y"),     # 15/01/24
                current_dt.strftime("%d-%m-%y"),     # 15-01-24
            ])
            
            # Move to next day (but limit to avoid too many patterns)
            current_dt += timedelta(days=1)
            if len(patterns) > 1000:  # Limit patterns for performance
                break
        
        # Add month/year patterns if range spans multiple months
        months_in_range = set()
        current_dt = start_dt
        while current_dt <= end_dt:
            month_year = (current_dt.month, current_dt.year)
            if month_year not in months_in_range:
                months_in_range.add(month_year)
                patterns.extend([
                    f"{current_dt.month:02d}/{current_dt.year}",
                    f"{current_dt.month}/{current_dt.year}",
                    f"{current_dt.year}-{current_dt.month:02d}",
                    f"{calendar.month_abbr[current_dt.month].lower()} {current_dt.year}",
                    f"{calendar.month_name[current_dt.month].lower()} {current_dt.year}",
                ])
            
            # Move to next month
            if current_dt.month == 12:
                current_dt = current_dt.replace(year=current_dt.year + 1, month=1)
            else:
                current_dt = current_dt.replace(month=current_dt.month + 1)
            
            if current_dt > end_dt:
                break
        
        return patterns
    
    def _has_relevant_dates(self, chunk: str, date_patterns: List[str]) -> bool:
        """Quick check if chunk contains dates from the filing period."""
        chunk_lower = chunk.lower()
        
        # Check for any date patterns
        for pattern in date_patterns[:20]:  # Check first 20 patterns for performance
            if pattern.lower() in chunk_lower:
                return True
        
        # Check for date-related keywords that might need AI analysis
        date_keywords = ['date', 'invoice date', 'transaction date', 'bill date', 'dated']
        return any(keyword in chunk_lower for keyword in date_keywords)
    
    def _ai_date_filtering(self, relevant_chunks: List[tuple], filing_month: str, filing_year: str) -> Dict[str, Any]:
        """Use AI to extract and validate dates from chunks."""
        
        batch_prompt = f"""Extract and validate transaction dates from these document chunks for GST filing.

Filing Period: {filing_month} {filing_year}

Instructions:
1. Look for invoice dates, transaction dates, bill dates, or any date indicating when the transaction occurred
2. Only include chunks with transactions from {filing_month} {filing_year}
3. Ignore future dates or dates from other months/years
4. Consider various date formats: DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, Month YYYY, etc.

Chunks to analyze:
"""
        
        for i, (chunk_idx, chunk) in enumerate(relevant_chunks):
            batch_prompt += f"\nChunk {i+1} (Index {chunk_idx}): {chunk[:400]}...\n"
        
        batch_prompt += f"""
Respond with JSON only:
{{
  "filtered_results": [
    {{
      "chunk_index": 0,
      "contains_filing_period_dates": true/false,
      "extracted_dates": ["DD/MM/YYYY", "DD/MM/YYYY"],
      "confidence": 0.0-1.0,
      "reason": "explanation"
    }}
  ],
  "summary": {{
    "total_chunks_analyzed": 0,
    "chunks_with_filing_period_dates": 0,
    "filing_period": "{filing_month} {filing_year}"
  }}
}}"""

        try:
            response = self.model.generate_content(batch_prompt)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                result_data = json.loads(json_match.group())
                
                # Filter chunks based on AI analysis
                filtered_chunk_indices = []
                for result in result_data.get("filtered_results", []):
                    if result.get("contains_filing_period_dates", False):
                        filtered_chunk_indices.append(result["chunk_index"])
                
                return {
                    "filtered_chunks": filtered_chunk_indices,
                    "filing_period": f"{filing_month} {filing_year}",
                    "total_original_chunks": len(relevant_chunks),
                    "total_filtered_chunks": len(filtered_chunk_indices),
                    "ai_analysis": result_data,
                    "notes": f"AI filtered {len(filtered_chunk_indices)} chunks for {filing_month} {filing_year}"
                }
            
        except Exception as e:
            print(f"AI date filtering failed: {e}")
        
        # Fallback: return all relevant chunks
        return {
            "filtered_chunks": [chunk_idx for chunk_idx, _ in relevant_chunks],
            "filing_period": f"{filing_month} {filing_year}",
            "total_original_chunks": len(relevant_chunks),
            "total_filtered_chunks": len(relevant_chunks),
            "notes": f"Fallback: returned all {len(relevant_chunks)} potentially relevant chunks"
        }
    
    def _ai_date_range_filtering(self, relevant_chunks: List[tuple], start_date: str, end_date: str) -> Dict[str, Any]:
        """Use AI to extract and validate dates from chunks for custom date range."""
        
        batch_prompt = f"""Extract and validate transaction dates from these document chunks for GST filing.

Date Range: {start_date} to {end_date}

Instructions:
1. Look for invoice dates, transaction dates, bill dates, or any date indicating when the transaction occurred
2. Only include chunks with transactions between {start_date} and {end_date} (inclusive)
3. Consider various date formats: DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, YYYY-MM-DD, etc.
4. Ignore dates outside the specified range

Chunks to analyze:
"""
        
        for i, (chunk_idx, chunk) in enumerate(relevant_chunks):
            batch_prompt += f"\nChunk {i+1} (Index {chunk_idx}): {chunk[:400]}...\n"
        
        batch_prompt += f"""
Respond with JSON only:
{{
  "filtered_results": [
    {{
      "chunk_index": 0,
      "contains_date_range_dates": true/false,
      "extracted_dates": ["DD/MM/YYYY", "DD/MM/YYYY"],
      "confidence": 0.0-1.0,
      "reason": "explanation"
    }}
  ],
  "summary": {{
    "total_chunks_analyzed": 0,
    "chunks_with_date_range_dates": 0,
    "date_range": "{start_date} to {end_date}"
  }}
}}"""

        try:
            response = self.model.generate_content(batch_prompt)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                result_data = json.loads(json_match.group())
                
                # Filter chunks based on AI analysis
                filtered_chunk_indices = []
                for result in result_data.get("filtered_results", []):
                    if result.get("contains_date_range_dates", False):
                        filtered_chunk_indices.append(result["chunk_index"])
                
                return {
                    "filtered_chunks": filtered_chunk_indices,
                    "filing_period": f"{start_date} to {end_date}",
                    "total_original_chunks": len(relevant_chunks),
                    "total_filtered_chunks": len(filtered_chunk_indices),
                    "ai_analysis": result_data,
                    "notes": f"AI filtered {len(filtered_chunk_indices)} chunks for date range {start_date} to {end_date}"
                }
            
        except Exception as e:
            print(f"AI date range filtering failed: {e}")
        
        # Fallback: return all relevant chunks
        return {
            "filtered_chunks": [chunk_idx for chunk_idx, _ in relevant_chunks],
            "filing_period": f"{start_date} to {end_date}",
            "total_original_chunks": len(relevant_chunks),
            "total_filtered_chunks": len(relevant_chunks),
            "notes": f"Fallback: returned all {len(relevant_chunks)} potentially relevant chunks for date range"
        }
