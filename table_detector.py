#!/usr/bin/env python3
"""
Table Detector for PageFinder
=============================

This module provides fast table detection capabilities for finding tables of interest
in processed PDF documents. It replaces Abby FlexiLayout with a Pythonic solution
that works with the LMDB database.
"""

import re
from typing import List, Dict, Optional, Tuple, Set
import attrs
from enum import Enum
import json
from pathlib import Path

class MatchStrategy(Enum):
    """Different strategies for determining if a table is found"""
    ALL_ELEMENTS = "all_elements"           # All text elements must be found
    MIN_COUNT = "min_count"                 # Minimum number of elements must be found
    MIN_PERCENTAGE = "min_percentage"       # Minimum percentage of elements must be found
    WEIGHTED_SCORE = "weighted_score"       # Weighted scoring system

@attrs.define
class TextElement:
    """A text element to search for in documents"""
    search_text: str = attrs.field(validator=attrs.validators.instance_of(str))
    max_errors: int = attrs.field(default=2, validator=attrs.validators.ge(0))
    max_error_rate: float = attrs.field(default=0.3, validator=attrs.validators.and_(attrs.validators.ge(0.0), attrs.validators.le(1.0)))
    match_case: bool = attrs.field(default=False, validator=attrs.validators.instance_of(bool))
    weight: float = attrs.field(default=1.0, validator=attrs.validators.gt(0.0))
    description: str = attrs.field(default="", validator=attrs.validators.instance_of(str))
    search_pattern: re.Pattern = attrs.field(init=False, default=None)
    
    def __attrs_post_init__(self):
        """Validate and prepare the text element after initialization"""
        if not self.search_text.strip():
            raise ValueError("search_text cannot be empty")
        
        # Prepare search pattern
        if self.match_case:
            self.search_pattern = re.compile(re.escape(self.search_text))
        else:
            self.search_pattern = re.compile(re.escape(self.search_text), re.IGNORECASE)

@attrs.define
class TableDefinition:
    """Definition of a table to search for"""
    name: str = attrs.field(validator=attrs.validators.instance_of(str))
    text_elements: List[TextElement] = attrs.field(validator=attrs.validators.instance_of(list))
    match_strategy: MatchStrategy = attrs.field(default=MatchStrategy.MIN_COUNT, validator=attrs.validators.instance_of(MatchStrategy))
    min_elements: int = attrs.field(default=3, validator=attrs.validators.ge(1))
    min_percentage: float = attrs.field(default=0.6, validator=attrs.validators.and_(attrs.validators.ge(0.0), attrs.validators.le(1.0)))
    min_score: float = attrs.field(default=0.7, validator=attrs.validators.and_(attrs.validators.ge(0.0), attrs.validators.le(1.0)))
    description: str = attrs.field(default="", validator=attrs.validators.instance_of(str))
    
    def __attrs_post_init__(self):
        """Validate table definition after initialization"""
        if not self.text_elements:
            raise ValueError("Table must have at least one text element")
        
        if self.match_strategy == MatchStrategy.MIN_COUNT:
            if self.min_elements > len(self.text_elements):
                raise ValueError(f"min_elements ({self.min_elements}) cannot exceed total elements ({len(self.text_elements)})")
        
        if self.match_strategy == MatchStrategy.MIN_PERCENTAGE:
            if not 0.0 <= self.min_percentage <= 1.0:
                raise ValueError("min_percentage must be between 0.0 and 1.0")

@attrs.define
class SearchResult:
    """Result of searching for a text element in a page"""
    element: TextElement = attrs.field(validator=attrs.validators.instance_of(TextElement))
    found: bool = attrs.field(validator=attrs.validators.instance_of(bool))
    page_num: int = attrs.field(validator=attrs.validators.instance_of(int))
    matches: List[Tuple[int, str]] = attrs.field(default=attrs.Factory(list))  # (position, matched_text)
    error_rate: float = attrs.field(default=0.0, validator=attrs.validators.and_(attrs.validators.ge(0.0), attrs.validators.le(1.0)))
    score: float = attrs.field(default=0.0, validator=attrs.validators.and_(attrs.validators.ge(0.0), attrs.validators.le(1.0)))

@attrs.define
class TableSearchResult:
    """Result of searching for a table in a document"""
    table_name: str = attrs.field(validator=attrs.validators.instance_of(str))
    document_name: str = attrs.field(validator=attrs.validators.instance_of(str))
    found: bool = attrs.field(validator=attrs.validators.instance_of(bool))
    file_path: str = attrs.field(default="", validator=attrs.validators.instance_of(str))
    pages_found: List[int] = attrs.field(default=attrs.Factory(list), validator=attrs.validators.instance_of(list))
    element_results: List[SearchResult] = attrs.field(default=attrs.Factory(list), validator=attrs.validators.instance_of(list))
    confidence_score: float = attrs.field(default=0.0, validator=attrs.validators.and_(attrs.validators.ge(0.0), attrs.validators.le(1.0)))
    match_details: str = attrs.field(default="", validator=attrs.validators.instance_of(str))

class TableDetector:
    """Fast table detection system for processed PDF documents"""
    
    def __init__(self, db_connection):
        """Initialize the table detector with database connection"""
        self.db = db_connection
        self.tables: List[TableDefinition] = []
    
    def add_table_definition(self, table_def: TableDefinition):
        """Add a table definition to search for"""
        self.tables.append(table_def)
    
    def add_table_from_dict(self, table_dict: Dict):
        """Add a table definition from a dictionary"""
        # Convert text elements
        text_elements = []
        for elem_dict in table_dict.get('text_elements', []):
            elem = TextElement(**elem_dict)
            text_elements.append(elem)
        
        # Create table definition
        table_def = TableDefinition(
            name=table_dict['name'],
            text_elements=text_elements,
            match_strategy=MatchStrategy(table_dict.get('match_strategy', 'min_count')),
            min_elements=table_dict.get('min_elements', 3),
            min_percentage=table_dict.get('min_percentage', 0.6),
            min_score=table_dict.get('min_score', 0.7),
            description=table_dict.get('description', '')
        )
        
        self.add_table_definition(table_def)
    
    def load_table_definitions(self, config_file: str):
        """Load table definitions from a JSON configuration file"""
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        for table_dict in config.get('tables', []):
            self.add_table_from_dict(table_dict)
    
    def search_text_element(self, element: TextElement, text: str, page_num: int) -> SearchResult:
        """Search for a single text element in page text"""
        if not text.strip():
            return SearchResult(
                element=element,
                found=False,
                page_num=page_num,
                matches=[],
                error_rate=1.0,
                score=0.0
            )
        
        # Find all matches
        matches = []
        for match in element.search_pattern.finditer(text):
            matched_text = match.group()
            position = match.start()
            matches.append((position, matched_text))
        
        if not matches:
            return SearchResult(
                element=element,
                found=False,
                page_num=page_num,
                matches=[],
                error_rate=1.0,
                score=0.0
            )
        
        # Calculate error rate and score
        best_match = min(matches, key=lambda x: len(x[1]))
        matched_text = best_match[1]
        search_text = element.search_text
        
        if element.match_case:
            error_rate = 1 - (len(matched_text) / len(search_text))
        else:
            # Case-insensitive comparison
            error_rate = 1 - (len(matched_text.lower()) / len(search_text.lower()))
        
        # Check if within error limits
        found = (error_rate <= element.max_error_rate and 
                len(matches) <= element.max_errors + 1)
        
        # Calculate confidence score
        score = max(0.0, 1.0 - error_rate) * element.weight
        
        return SearchResult(
            element=element,
            found=found,
            page_num=page_num,
            matches=matches,
            error_rate=error_rate,
            score=score
        )
    
    def is_table_found(self, table_def: TableDefinition, element_results: List[SearchResult]) -> Tuple[bool, float, str]:
        """Determine if a table is found based on the match strategy"""
        found_elements = [r for r in element_results if r.found]
        total_elements = len(element_results)
 
        # Guard: no results collected (nothing matched anywhere)
        if total_elements == 0:
            # Consider as not found with zero confidence
            details = f"Found 0/{len(table_def.text_elements)} elements"
            return False, 0.0, details
        found_count = len(found_elements)
        
        if table_def.match_strategy == MatchStrategy.ALL_ELEMENTS:
            found = found_count == total_elements
            score = found_count / total_elements
            details = f"Found {found_count}/{total_elements} elements"
            
        elif table_def.match_strategy == MatchStrategy.MIN_COUNT:
            found = found_count >= table_def.min_elements
            score = found_count / total_elements
            details = f"Found {found_count}/{total_elements} elements (min: {table_def.min_elements})"
            
        elif table_def.match_strategy == MatchStrategy.MIN_PERCENTAGE:
            percentage = found_count / total_elements
            found = percentage >= table_def.min_percentage
            score = percentage
            details = f"Found {found_count}/{total_elements} elements ({percentage:.1%}, min: {table_def.min_percentage:.1%})"
            
        elif table_def.match_strategy == MatchStrategy.WEIGHTED_SCORE:
            total_score = sum(r.score for r in element_results)
            max_possible_score = sum(e.weight for e in table_def.text_elements)
            score = total_score / max_possible_score if max_possible_score > 0 else 0.0
            found = score >= table_def.min_score
            details = f"Weighted score: {score:.3f} (min: {table_def.min_score:.3f})"
        
        return found, score, details
    
    def search_document_for_tables(self, document_name: str, min_confidence: float = 0.0) -> List[TableSearchResult]:
        """Search a single document for all defined tables - aggregating pages per table"""
        results = []
        
        # Get document pages from database
        try:
            pages = self.db.get_document_pages(document_name)
        except Exception as e:
            print(f"Error accessing document {document_name}: {e}")
            return results
        
        # Get document metadata for file path
        metadata = self.db.get_document_metadata(document_name)
        file_path = metadata.get('file_path', '') if metadata else ''

        
        # Convert to absolute path and normalize backslashes
        if file_path:
            try:
                # Convert to absolute path
                abs_path = Path(file_path).resolve()
                # Convert to string with single backslashes
                file_path = str(abs_path).replace('\\', '/')
            except Exception:
                # If path resolution fails, just normalize the backslashes
                file_path = file_path.replace('\\', '/')
        
        for table_def in self.tables:
            # Track all pages where this table is found
            found_pages = []
            all_element_results = []
            page_confidences = []
            page_details_list = []
            
            for page_num, page_text in pages.items():
                # Search this specific page for all text elements
                page_element_results = []
                
                for element in table_def.text_elements:
                    result = self.search_text_element(element, page_text, page_num)
                    page_element_results.append(result)
                
                # Check if THIS PAGE contains enough elements to qualify as the table
                page_found, page_confidence, page_details = self.is_table_found(table_def, page_element_results)
                
                # Only include results that meet the confidence threshold
                if page_found and page_confidence >= min_confidence:
                    found_pages.append(page_num)
                    all_element_results.extend(page_element_results)
                    page_confidences.append(page_confidence)
                    page_details_list.append(f"Page {page_num}: {page_details}")
            
            # If table was found on any pages, create a single result
            if found_pages:
                # Calculate overall confidence as average of page confidences
                overall_confidence = sum(page_confidences) / len(page_confidences) if page_confidences else 0.0
                
                # Combine match details from all pages
                combined_details = "; ".join(page_details_list)
                
                # Create single result for this table in this document
                table_result = TableSearchResult(
                    table_name=table_def.name,
                    document_name=document_name,
                    file_path=file_path,
                    found=True,
                    pages_found=sorted(found_pages),  # All pages where table was found
                    element_results=all_element_results,
                    confidence_score=overall_confidence,
                    match_details=combined_details
                )
                results.append(table_result)
        
        return results
    
    def search_all_documents(self, document_names: Optional[List[str]] = None, min_confidence: float = 0.0) -> List[TableSearchResult]:
        """Search all documents for tables"""
        if document_names is None:
            document_names = self.db.list_all_docs()
        
        all_results = []
        
        for doc_name in document_names:
            doc_results = self.search_document_for_tables(doc_name, min_confidence)
            all_results.extend(doc_results)
        
        return all_results
    
    def get_summary_report(self, results: List[TableSearchResult]) -> Dict:
        """Generate a summary report of table search results"""
        summary = {
            'total_documents_searched': len(set(r.document_name for r in results)),
            'total_tables_found': len([r for r in results if r.found]),
            'tables_by_document': {},
            'tables_by_type': {}
        }
        
        # Group by document
        for result in results:
            doc_name = result.document_name
            if doc_name not in summary['tables_by_document']:
                summary['tables_by_document'][doc_name] = []
            
            if result.found:
                summary['tables_by_document'][doc_name].append({
                    'table_name': result.table_name,
                    'pages': result.pages_found,
                    'confidence': result.confidence_score
                })
        
        # Group by table type
        for result in results:
            table_name = result.table_name
            if table_name not in summary['tables_by_type']:
                summary['tables_by_type'][table_name] = {
                    'found_in_documents': [],
                    'total_occurrences': 0
                }
            
            if result.found:
                summary['tables_by_type'][table_name]['found_in_documents'].append({
                    'document': result.document_name,
                    'pages': result.pages_found,
                    'confidence': result.confidence_score
                })
                summary['tables_by_type'][table_name]['total_occurrences'] += 1
        
        return summary
