"""Date-based filtering agent for GST filing periods."""

import google.generativeai as genai
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import json
import re
from datetime import datetime, date, timedelta
import calendar
from dateutil import parser as date_parser
import locale

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
        date_patterns = []  # Initialize date_patterns
        period_desc = ""
        
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
                
                # Generate date patterns for the date range
                date_patterns = self._generate_date_range_patterns(start_dt, end_dt)
                period_desc = f"{start_date} to {end_date}"
                
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
        current_dt = start_dt
        
        while current_dt <= end_dt:
            # Add various date formats for each day in the range
            patterns.extend([
                current_dt.strftime("%d/%m/%Y"),
                current_dt.strftime("%d-%m-%Y"),
                current_dt.strftime("%d.%m.%Y"),
                current_dt.strftime("%Y-%m-%d"),
                current_dt.strftime("%d %B %Y"),
                current_dt.strftime("%d %b %Y"),
                current_dt.strftime("%B %d, %Y"),
                current_dt.strftime("%b %d, %Y"),
                current_dt.strftime("%d-%b-%Y"),  # 24-Aug-2025
                current_dt.strftime("%d-%B-%Y"),  # 24-August-2025
                current_dt.strftime("%b-%d-%Y"),  # Aug-24-2025
                current_dt.strftime("%B-%d-%Y")   # August-24-2025
            ])
            current_dt += timedelta(days=1)
            
            # Limit patterns to avoid performance issues
            if len(patterns) > 1000:
                break
                
        return patterns
    
    def _extract_all_dates_from_chunk(self, chunk: str) -> List[str]:
        """Extract all possible dates from a chunk using comprehensive regex patterns."""
        found_dates = []
        
        # Comprehensive date regex patterns
        date_patterns = [
            # DD/MM/YYYY variations
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b',
            r'\b\d{1,2}\.\d{1,2}\.\d{4}\b',
            # YYYY-MM-DD variations
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
            r'\b\d{4}\.\d{1,2}\.\d{1,2}\b',
            # DD-MMM-YYYY variations (like 24-Aug-2025)
            r'\b\d{1,2}[-/]\w{3,9}[-/]\d{4}\b',
            r'\b\d{1,2}\s+\w{3,9}\s+\d{4}\b',
            # MMM-DD-YYYY variations
            r'\b\w{3,9}[-/]\d{1,2}[-/]\d{4}\b',
            r'\b\w{3,9}\s+\d{1,2}\s*,?\s*\d{4}\b',
            # DD MMM YYYY (with comma)
            r'\b\d{1,2}\s+\w{3,9}\s*,\s*\d{4}\b',
            # MMM YYYY (month year only)
            r'\b\w{3,9}\s+\d{4}\b',
            # YYYY MMM (year month)
            r'\b\d{4}\s+\w{3,9}\b',
            # Indian date formats
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2}\b',  # DD/MM/YY
            # Time with dates
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\s+\d{1,2}:\d{2}(?::\d{2})?\b',
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, chunk, re.IGNORECASE)
            found_dates.extend(matches)
        
        return found_dates
    
    def _parse_date_flexible(self, date_str: str) -> Optional[datetime]:
        """Parse date string using multiple methods for maximum compatibility."""
        if not date_str or not date_str.strip():
            return None
            
        date_str = date_str.strip()
        
        # Try dateutil parser first (handles most formats)
        try:
            return date_parser.parse(date_str, fuzzy=True)
        except:
            pass
        
        # Manual parsing for specific formats
        common_formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y',
            '%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d',
            '%d %b %Y', '%d-%b-%Y', '%d/%b/%Y',
            '%b %d, %Y', '%b-%d-%Y', '%b/%d/%Y',
            '%d %B %Y', '%d-%B-%Y', '%d/%B/%Y',
            '%B %d, %Y', '%B-%d-%Y', '%B/%d/%Y',
            '%d/%m/%y', '%d-%m-%y', '%d.%m.%y',
            '%m/%d/%Y', '%m-%d-%Y', '%m.%d.%Y',
            '%Y%m%d', '%d%m%Y',
        ]
        
        for fmt in common_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        
        return None
    
    def _is_date_in_range(self, date_obj: datetime, start_date: str, end_date: str) -> bool:
        """Check if a date falls within the specified range."""
        try:
            start_dt = self._parse_date_flexible(start_date)
            end_dt = self._parse_date_flexible(end_date)
            
            if not start_dt or not end_dt:
                return False
                
            return start_dt.date() <= date_obj.date() <= end_dt.date()
        except:
            return False
    
    def _has_relevant_dates(self, chunk: str, date_patterns: List[str]) -> bool:
        """Enhanced date detection using multiple methods."""
        chunk_lower = chunk.lower()
        
        # Method 1: Check for specific date patterns
        for pattern in date_patterns[:20]:
            if pattern.lower() in chunk_lower:
                return True
        
        # Method 2: Extract all dates and check if any exist
        extracted_dates = self._extract_all_dates_from_chunk(chunk)
        if extracted_dates:
            return True
        
        # Method 3: Check for date-related keywords
        date_keywords = [
            'date', 'invoice date', 'transaction date', 'bill date', 'dated',
            'invoice no', 'receipt date', 'payment date', 'due date',
            'issued on', 'generated on', 'created on', 'timestamp'
        ]
        
        return any(keyword in chunk_lower for keyword in date_keywords)
    
    def _ai_date_filtering(self, relevant_chunks: List[tuple], filing_month: str, filing_year: str) -> Dict[str, Any]:
        """Use AI to extract and validate dates from chunks."""
        
        # Pre-filter chunks using local date parsing
        pre_filtered_chunks = []
        for chunk_idx, chunk in relevant_chunks:
            extracted_dates = self._extract_all_dates_from_chunk(chunk)
            chunk_has_valid_dates = False
            
            for date_str in extracted_dates:
                parsed_date = self._parse_date_flexible(date_str)
                if parsed_date:
                    # Check if date matches filing period
                    if (parsed_date.strftime('%B').lower() == filing_month.lower() and 
                        str(parsed_date.year) == filing_year):
                        chunk_has_valid_dates = True
                        break
            
            if chunk_has_valid_dates:  # Only include if valid dates found
                pre_filtered_chunks.append((chunk_idx, chunk))
        
        # If pre-filtering found matches, use those; otherwise use AI as fallback
        if pre_filtered_chunks:
            return {
                "filtered_chunks": [chunk_idx for chunk_idx, _ in pre_filtered_chunks],
                "filing_period": f"{filing_month} {filing_year}",
                "total_original_chunks": len(relevant_chunks),
                "total_filtered_chunks": len(pre_filtered_chunks),
                "notes": f"Pre-filtered {len(pre_filtered_chunks)} chunks using local date parsing for {filing_month} {filing_year}"
            }
        
        batch_prompt = f"""Extract and validate transaction dates from these document chunks for GST filing.

Filing Period: {filing_month} {filing_year}

Instructions:
1. Look for ANY date formats: DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, DD-MMM-YYYY (like 24-Aug-2025), MMM DD YYYY, Month YYYY, etc.
2. Extract ALL dates found in each chunk
3. Only include chunks with transactions from {filing_month} {filing_year}
4. Be flexible with date parsing - consider abbreviations, full month names, different separators
5. Pay special attention to dates in tables, invoice headers, and transaction records

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
                
                # Filter chunks based on AI analysis - map back to original chunk indices
                filtered_chunk_indices = []
                for result in result_data.get("filtered_results", []):
                    if result.get("contains_filing_period_dates", False):
                        # Get the original chunk index from relevant_chunks
                        result_idx = result["chunk_index"]
                        if result_idx < len(relevant_chunks):
                            original_chunk_idx = relevant_chunks[result_idx][0]
                            filtered_chunk_indices.append(original_chunk_idx)
                
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
        
        # Pre-filter chunks using local date parsing for date range
        pre_filtered_chunks = []
        for chunk_idx, chunk in relevant_chunks:
            extracted_dates = self._extract_all_dates_from_chunk(chunk)
            chunk_has_valid_dates = False
            
            for date_str in extracted_dates:
                parsed_date = self._parse_date_flexible(date_str)
                if parsed_date and self._is_date_in_range(parsed_date, start_date, end_date):
                    chunk_has_valid_dates = True
                    break
            
            if chunk_has_valid_dates:  # Only include if valid dates found
                pre_filtered_chunks.append((chunk_idx, chunk))
        
        # If pre-filtering found matches, use those; otherwise use AI as fallback
        if pre_filtered_chunks:
            return {
                "filtered_chunks": [chunk_idx for chunk_idx, _ in pre_filtered_chunks],
                "filing_period": f"{start_date} to {end_date}",
                "total_original_chunks": len(relevant_chunks),
                "total_filtered_chunks": len(pre_filtered_chunks),
                "notes": f"Pre-filtered {len(pre_filtered_chunks)} chunks using local date parsing for range {start_date} to {end_date}"
            }
        
        batch_prompt = f"""Extract and validate transaction dates from these document chunks for GST filing.

Date Range: {start_date} to {end_date}

Instructions:
1. Look for ANY date formats: DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, YYYY-MM-DD, DD-MMM-YYYY (like 24-Aug-2025), MMM DD YYYY, etc.
2. Extract ALL dates found in each chunk
3. Only include chunks with transactions between {start_date} and {end_date} (inclusive)
4. Be flexible with date parsing - consider abbreviations, full month names, different separators
5. Pay special attention to dates in tables, invoice headers, and transaction records

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
                
                # Filter chunks based on AI analysis - map back to original chunk indices
                filtered_chunk_indices = []
                for result in result_data.get("filtered_results", []):
                    if result.get("contains_date_range_dates", False):
                        # Get the original chunk index from relevant_chunks
                        result_idx = result["chunk_index"]
                        if result_idx < len(relevant_chunks):
                            original_chunk_idx = relevant_chunks[result_idx][0]
                            filtered_chunk_indices.append(original_chunk_idx)
                
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
