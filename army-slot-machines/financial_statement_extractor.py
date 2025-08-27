import pdfplumber
import pandas as pd

import re
from typing import Dict, List

class FinancialStatementExtractor:
    """
    A comprehensive financial statement extractor for PDF documents.
    
    This class can automatically detect and extract data from three types of financial statements:
    - Branch breakdown statements (showing data by Army, Navy, USMC)
    - Operating results statements (showing budget vs actual data)
    - Balance sheet statements (showing assets, liabilities, equity)
    
    The extractor uses pdfplumber to parse PDF content and provides structured data output
    in various formats including dictionaries, DataFrames, and summary reports.
    
    Example:
        >>> extractor = FinancialStatementExtractor("financial_statement.pdf")
        >>> statement_type = extractor.detect_statement_type()
        >>> financial_data = extractor.extract_financial_data()
        >>> summary = extractor.generate_summary_report()
    """
    
    def __init__(self, pdf_path: str):
        """
        Initialize the financial statement extractor.
        
        Args:
            pdf_path (str): Path to the PDF file containing the financial statement.
                          Must be a valid path to a readable PDF file.
        
        Attributes:
            pdf_path (str): Stored path to the PDF file
            pages_data (List): Storage for page-specific data (currently unused)
            statement_type (str): Detected statement type, set automatically when needed
        """
        self.pdf_path = pdf_path
        self.pages_data = []
        self.statement_type = None  # Will be detected automatically
    
    def extract_all_text(self) -> str:
        """
        Extract all text content from the PDF file.
        
        Concatenates text from all pages in the PDF document with newline separators.
        
        Returns:
            str: Complete text content of the PDF with pages separated by newlines.
                Returns empty string if PDF cannot be read or contains no text.
        
        Raises:
            FileNotFoundError: If the PDF file path does not exist.
            Exception: If the PDF file is corrupted or cannot be opened.
        """
        full_text = ""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
        return full_text
    
    def extract_tables(self) -> List[pd.DataFrame]:
        """
        Extract all tables from the PDF as pandas DataFrames.
        
        Processes each page to find tabular data and converts it to DataFrames.
        The first row of each table is used as column headers.
        
        Returns:
            List[pd.DataFrame]: List of DataFrames, one for each table found.
                                Each DataFrame has a 'name' attribute indicating its source
                                (e.g., "Page_1_Table_1"). Returns empty list if no tables found.
        
        Note:
            Only non-empty tables are processed. Tables with no data are skipped.
        """
        tables = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_tables = page.extract_tables()
                for j, table in enumerate(page_tables):
                    if table:  # Only process non-empty tables
                        df = pd.DataFrame(table[1:], columns=table[0])  # First row as headers
                        df.name = f"Page_{i+1}_Table_{j+1}"
                        tables.append(df)
        return tables
    
    def detect_statement_type(self) -> str:
        """
        Automatically detect the type of financial statement in the PDF.
        
        Analyzes the text content to identify key phrases that indicate the statement type.
        
        Returns:
            str: One of the following statement types:
                - "branch_breakdown": Contains "Branch of Service" - shows data by military branch
                - "operating_results": Contains "Actual vs Budget" - shows budget vs actual performance
                - "balance_sheet": Contains "Statement of Financial Condition" - shows assets/liabilities
                - "unknown": None of the above patterns found
        
        Example:
            >>> extractor = FinancialStatementExtractor("statement.pdf")
            >>> stmt_type = extractor.detect_statement_type()
            >>> print(stmt_type)  # "operating_results"
        """
        with pdfplumber.open(self.pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
            
            if "Branch of Service" in full_text:
                return "branch_breakdown"
            elif "Actual vs Budget" in full_text:
                return "operating_results"
            elif "Statement of Financial Condition" in full_text:
                return "balance_sheet"
            else:
                return "unknown"
    
    def extract_operating_results(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        Extract budget vs actual operating results data from the PDF.
        
        Parses operating statements that contain March and YTD (Year-to-Date) budget vs actual
        comparisons. Extracts revenue, expenses, and income data with variance calculations.
        
        Returns:
            Dict[str, Dict[str, Dict[str, float]]]: Nested dictionary with structure:
                {
                    'revenue': {
                        'Item Name': {
                            'march_actual': float, 'march_budget': float, 'march_variance': float,
                            'ytd_actual': float, 'ytd_budget': float, 'ytd_variance': float
                        }
                    },
                    'direct_reimbursement': {...},
                    'net_revenue': {...},
                    'operating_expenses': {...},
                    'net_operating_income': {...},
                    'other_income': {...},
                    'net_income': {...},
                    'distributions': {...}
                }
        
        Note:
            Expects PDF to contain sections with 6-column format:
            Mar Actual, Mar Budget, Mar Variance, YTD Actual, YTD Budget, YTD Variance
        """
        operating_data = {
            'revenue': {},
            'direct_reimbursement': {},
            'net_revenue': {},
            'operating_expenses': {},
            'net_operating_income': {},
            'other_income': {},
            'net_income': {},
            'distributions': {}
        }
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                
                # Extract different sections of the operating statement
                revenue_section = self._extract_section(text, "Revenue", "Direct NAFI")
                operating_data['revenue'].update(self._parse_budget_actual_items(revenue_section))
                
                reimbursement_section = self._extract_section(text, "Direct NAFI", "Net Revenue")
                operating_data['direct_reimbursement'].update(self._parse_budget_actual_items(reimbursement_section))
                
                expenses_section = self._extract_section(text, "Operating Expenses", "Total Operating Expenses")
                operating_data['operating_expenses'].update(self._parse_budget_actual_items(expenses_section))
                
                # Extract summary lines
                net_revenue = self._extract_summary_line(text, "Net Revenue")
                if net_revenue:
                    operating_data['net_revenue']['Net Revenue'] = net_revenue
                
                net_operating = self._extract_summary_line(text, "Net Operating Income")
                if net_operating:
                    operating_data['net_operating_income']['Net Operating Income'] = net_operating
                
                interest_revenue = self._extract_summary_line(text, "Interest Revenue")
                if interest_revenue:
                    operating_data['other_income']['Interest Revenue'] = interest_revenue
                
                net_income = self._extract_summary_line(text, "Net Income/(Loss)")
                if net_income:
                    operating_data['net_income']['Net Income'] = net_income
        
        return operating_data
    
    def _parse_budget_actual_items(self, section_text: str) -> Dict[str, Dict[str, float]]:
        """
        Parse line items with 6-column budget vs actual format.
        
        Extracts financial line items that contain March and YTD budget vs actual data.
        Uses regex to identify lines with 6 numeric values and parses them into structured data.
        
        Args:
            section_text (str): Text section containing financial line items to parse.
        
        Returns:
            Dict[str, Dict[str, float]]: Dictionary mapping item names to their financial data:
                {
                    'Item Name': {
                        'march_actual': float, 'march_budget': float, 'march_variance': float,
                        'ytd_actual': float, 'ytd_budget': float, 'ytd_variance': float
                    }
                }
        
        Note:
            - Expects 6 columns: Mar Actual, Mar Budget, Mar Variance, YTD Actual, YTD Budget, YTD Variance
            - Handles negative amounts (indicated by trailing '-')
            - Skips separator lines (starting with '-' or '=')
        """
        items = {}
        lines = section_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('-') or line.startswith('='):
                continue
            
            # Look for lines with multiple financial amounts (6 columns expected)
            # Pattern: Item Name followed by 6 numeric values
            amounts = re.findall(r'[\d,]+\.?\d*-?', line)
            
            if len(amounts) >= 6:
                # Extract item name (everything before the first number)
                item_match = re.match(r'^(.+?)\s+[\d,]', line)
                if item_match:
                    item_name = item_match.group(1).strip()
                    
                    try:
                        # Parse the 6 columns: Mar Actual, Mar Budget, Mar Variance, YTD Actual, YTD Budget, YTD Variance
                        values = []
                        for amount_str in amounts[:6]:
                            clean_amount = amount_str.replace(',', '')
                            if clean_amount.endswith('-'):
                                values.append(-float(clean_amount[:-1]))
                            else:
                                values.append(float(clean_amount))
                        
                        items[item_name] = {
                            'march_actual': values[0],
                            'march_budget': values[1],
                            'march_variance': values[2],
                            'ytd_actual': values[3],
                            'ytd_budget': values[4],
                            'ytd_variance': values[5]
                        }
                    except (ValueError, IndexError):
                        continue
        
        return items
    
    def _extract_summary_line(self, text: str, line_identifier: str) -> Dict[str, float]:
        """
        Extract a single summary line with 6-column budget vs actual data.
        
        Searches for a specific line identifier and extracts the associated financial data
        in the same 6-column format as line items.
        
        Args:
            text (str): Full text to search within.
            line_identifier (str): Unique text to identify the target line (e.g., "Net Revenue").
        
        Returns:
            Dict[str, float]: Dictionary with budget vs actual data:
                {
                    'march_actual': float, 'march_budget': float, 'march_variance': float,
                    'ytd_actual': float, 'ytd_budget': float, 'ytd_variance': float
                }
                Returns empty dict if line not found or parsing fails.
        """
        lines = text.split('\n')
        
        for line in lines:
            if line_identifier in line:
                amounts = re.findall(r'[\d,]+\.?\d*-?', line)
                if len(amounts) >= 6:
                    try:
                        values = []
                        for amount_str in amounts[:6]:
                            clean_amount = amount_str.replace(',', '')
                            if clean_amount.endswith('-'):
                                values.append(-float(clean_amount[:-1]))
                            else:
                                values.append(float(clean_amount))
                        
                        return {
                            'march_actual': values[0],
                            'march_budget': values[1],
                            'march_variance': values[2],
                            'ytd_actual': values[3],
                            'ytd_budget': values[4],
                            'ytd_variance': values[5]
                        }
                    except (ValueError, IndexError):
                        continue
        return {}
    
    def extract_branch_breakdown(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        Extract branch of service breakdown data from the PDF.
        
        Parses financial statements that show data broken down by military branch
        (Army, Navy, USMC) with ARMP (Armed Forces Recreation and Morale Program) totals.
        
        Returns:
            Dict[str, Dict[str, Dict[str, float]]]: Nested dictionary with structure:
                {
                    'revenue': {
                        'Item Name': {
                            'armp_total': float, 'army': float, 'navy': float, 'usmc': float
                        }
                    },
                    'direct_reimbursement': {...},
                    'net_revenue': {...},
                    'operating_expenses': {...},
                    'net_operating_income': {...},
                    'other_income': {...},
                    'net_income': {...},
                    'distributions': {...}
                }
        
        Note:
            Expects PDF to contain sections with 4-column format:
            ARMP Total, Army, Navy, USMC
        """
        branch_data = {
            'revenue': {},
            'direct_reimbursement': {},
            'net_revenue': {},
            'operating_expenses': {},
            'net_operating_income': {},
            'other_income': {},
            'net_income': {},
            'distributions': {}
        }
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                
                # Extract different sections with branch breakdown
                revenue_section = self._extract_section(text, "Revenue", "Direct NAFI")
                branch_data['revenue'].update(self._parse_branch_items(revenue_section))
                
                reimbursement_section = self._extract_section(text, "Direct NAFI", "Net Revenue")
                branch_data['direct_reimbursement'].update(self._parse_branch_items(reimbursement_section))
                
                expenses_section = self._extract_section(text, "Operating Expenses", "Total Operating Expenses")
                branch_data['operating_expenses'].update(self._parse_branch_items(expenses_section))
                
                # Extract summary lines
                net_revenue = self._extract_branch_summary_line(text, "Net Revenue")
                if net_revenue:
                    branch_data['net_revenue']['Net Revenue'] = net_revenue
                
                net_operating = self._extract_branch_summary_line(text, "Net Operating Income")
                if net_operating:
                    branch_data['net_operating_income']['Net Operating Income'] = net_operating
                
                interest_revenue = self._extract_branch_summary_line(text, "Interest Revenue")
                if interest_revenue:
                    branch_data['other_income']['Interest Revenue'] = interest_revenue
                
                net_income = self._extract_branch_summary_line(text, "Net Income/(Loss)")
                if net_income:
                    branch_data['net_income']['Net Income'] = net_income
        
        return branch_data
    
    def _parse_branch_items(self, section_text: str) -> Dict[str, Dict[str, float]]:
        """
        Parse line items with 4-column branch breakdown format.
        
        Extracts financial line items that contain data broken down by military branch.
        Uses regex to identify lines with 4 numeric values and parses them into structured data.
        
        Args:
            section_text (str): Text section containing financial line items to parse.
        
        Returns:
            Dict[str, Dict[str, float]]: Dictionary mapping item names to their branch data:
                {
                    'Item Name': {
                        'armp_total': float, 'army': float, 'navy': float, 'usmc': float
                    }
                }
        
        Note:
            - Expects 4 columns: ARMP Total, Army, Navy, USMC
            - Handles negative amounts (indicated by trailing '-')
            - Skips separator lines (starting with '-' or '=')
        """
        items = {}
        lines = section_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('-') or line.startswith('='):
                continue
            
            # Look for lines with 4 financial amounts (ARMP Total, Army, Navy, USMC)
            amounts = re.findall(r'[\d,]+\.?\d*-?', line)
            
            if len(amounts) >= 4:
                # Extract item name (everything before the first number)
                item_match = re.match(r'^(.+?)\s+[\d,]', line)
                if item_match:
                    item_name = item_match.group(1).strip()
                    
                    try:
                        # Parse the 4 columns: ARMP Total, Army, Navy, USMC
                        values = []
                        for amount_str in amounts[:4]:
                            clean_amount = amount_str.replace(',', '')
                            if clean_amount.endswith('-'):
                                values.append(-float(clean_amount[:-1]))
                            else:
                                values.append(float(clean_amount))
                        
                        items[item_name] = {
                            'armp_total': values[0],
                            'army': values[1],
                            'navy': values[2],
                            'usmc': values[3]
                        }
                    except (ValueError, IndexError):
                        continue
        
        return items
    
    def _extract_branch_summary_line(self, text: str, line_identifier: str) -> Dict[str, float]:
        """
        Extract a single summary line with 4-column branch breakdown data.
        
        Searches for a specific line identifier and extracts the associated financial data
        in the same 4-column format as branch line items.
        
        Args:
            text (str): Full text to search within.
            line_identifier (str): Unique text to identify the target line (e.g., "Net Revenue").
        
        Returns:
            Dict[str, float]: Dictionary with branch breakdown data:
                {
                    'armp_total': float, 'army': float, 'navy': float, 'usmc': float
                }
                Returns empty dict if line not found or parsing fails.
        """
        lines = text.split('\n')
        
        for line in lines:
            if line_identifier in line:
                amounts = re.findall(r'[\d,]+\.?\d*-?', line)
                if len(amounts) >= 4:
                    try:
                        values = []
                        for amount_str in amounts[:4]:
                            clean_amount = amount_str.replace(',', '')
                            if clean_amount.endswith('-'):
                                values.append(-float(clean_amount[:-1]))
                            else:
                                values.append(float(clean_amount))
                        
                        return {
                            'armp_total': values[0],
                            'army': values[1],
                            'navy': values[2],
                            'usmc': values[3]
                        }
                    except (ValueError, IndexError):
                        continue
        return {}
    
    def calculate_branch_performance(self, branch_data: Dict) -> Dict[str, Dict[str, float]]:
        """
        Calculate branch performance metrics and percentages.
        
        Computes revenue share percentages and operating margins for each military branch
        based on the extracted branch breakdown data.
        
        Args:
            branch_data (Dict): Branch breakdown data from extract_branch_breakdown().
        
        Returns:
            Dict[str, Dict[str, float]]: Performance metrics by item and branch:
                {
                    'Revenue Item Name': {
                        'army_share_pct': float, 'navy_share_pct': float, 'usmc_share_pct': float
                    },
                    'Operating Margin': {
                        'army_margin_pct': float, 'navy_margin_pct': float, 'usmc_margin_pct': float,
                        'armp_margin_pct': float
                    }
                }
        
        Note:
            - Revenue share percentages show each branch's portion of total revenue
            - Operating margins calculated as net operating income / total revenue * 100
            - Returns empty dict if required data not available
        """
        performance = {}
        
        # Calculate revenue share by branch
        if 'revenue' in branch_data:
            revenue_items = branch_data['revenue']
            for item_name, values in revenue_items.items():
                if isinstance(values, dict) and values.get('armp_total', 0) != 0:
                    total = values['armp_total']
                    performance[item_name] = {
                        'army_share_pct': (values['army'] / total * 100) if total != 0 else 0,
                        'navy_share_pct': (values['navy'] / total * 100) if total != 0 else 0,
                        'usmc_share_pct': (values['usmc'] / total * 100) if total != 0 else 0
                    }
        
        # Calculate profit margins by branch
        if 'net_operating_income' in branch_data and 'revenue' in branch_data:
            net_income = branch_data['net_operating_income'].get('Net Operating Income', {})
            total_revenue = None
            
            # Find total revenue
            for item_name, values in branch_data['revenue'].items():
                if 'Total' in item_name or 'Gaming Machine Revenue' in item_name:
                    total_revenue = values
                    break
            
            if net_income and total_revenue:
                performance['Operating Margin'] = {
                    'army_margin_pct': (net_income.get('army', 0) / total_revenue.get('army', 1) * 100) if total_revenue.get('army', 0) != 0 else 0,
                    'navy_margin_pct': (net_income.get('navy', 0) / total_revenue.get('navy', 1) * 100) if total_revenue.get('navy', 0) != 0 else 0,
                    'usmc_margin_pct': (net_income.get('usmc', 0) / total_revenue.get('usmc', 1) * 100) if total_revenue.get('usmc', 0) != 0 else 0,
                    'armp_margin_pct': (net_income.get('armp_total', 0) / total_revenue.get('armp_total', 1) * 100) if total_revenue.get('armp_total', 0) != 0 else 0
                }
        
        return performance
    
    def calculate_variance_analysis(self, operating_data: Dict) -> Dict[str, Dict[str, float]]:
        """
        Calculate variance analysis percentages for operating results data.
        
        Computes variance percentages (actual vs budget) for both March and YTD periods
        across all categories and line items in the operating data.
        
        Args:
            operating_data (Dict): Operating results data from extract_operating_results().
        
        Returns:
            Dict[str, Dict[str, float]]: Variance analysis by category and item:
                {
                    'category_name': {
                        'Item Name': {
                            'march_variance_pct': float, 'ytd_variance_pct': float
                        }
                    }
                }
        
        Note:
            - Variance percentage = (variance / budget) * 100
            - Only processes items with budget data (march_budget, ytd_budget keys)
            - Returns 0% for items with zero budget to avoid division by zero
        """
        analysis = {}
        
        for category, items in operating_data.items():
            if category not in analysis:
                analysis[category] = {}
            
            for item_name, values in items.items():
                if isinstance(values, dict) and 'march_budget' in values:
                    march_budget = values['march_budget']
                    ytd_budget = values['ytd_budget']
                    
                    analysis[category][item_name] = {
                        'march_variance_pct': (values['march_variance'] / march_budget * 100) if march_budget != 0 else 0,
                        'ytd_variance_pct': (values['ytd_variance'] / ytd_budget * 100) if ytd_budget != 0 else 0
                    }
        
        return analysis
    def extract_financial_data(self) -> Dict[str, Dict[str, float]]:
        """
        Extract structured financial data with automatic statement type detection.
        
        This is the main extraction method that automatically detects the statement type
        and calls the appropriate specialized extraction method.
        
        Returns:
            Dict[str, Dict[str, float]]: Structured financial data. Format depends on statement type:
                - Branch breakdown: nested dict with branch data (armp_total, army, navy, usmc)
                - Operating results: nested dict with budget vs actual data (6 columns)
                - Balance sheet: nested dict with assets, liabilities, equity
                - Unknown: dict with single "unknown_data" key
        
        Example:
            >>> extractor = FinancialStatementExtractor("statement.pdf")
            >>> data = extractor.extract_financial_data()
            >>> print(data.keys())  # ['revenue', 'operating_expenses', ...]
        """
        statement_type = self.detect_statement_type()
        
        if statement_type == "branch_breakdown":
            return self.extract_branch_breakdown()
        elif statement_type == "operating_results":
            return self.extract_operating_results()
        elif statement_type == "balance_sheet":
            return self._extract_balance_sheet_data()
        else:
            return self._extract_generic_financial_data()
    
    def _extract_balance_sheet_data(self) -> Dict[str, Dict[str, float]]:
        """
        Extract balance sheet data from PDF (private method).
        
        Parses traditional balance sheet format with assets, liabilities, and equity sections.
        Uses simple item-amount parsing for each line.
        
        Returns:
            Dict[str, Dict[str, float]]: Balance sheet data with structure:
                {
                    'assets': {'Item Name': amount, ...},
                    'liabilities': {'Item Name': amount, ...},
                    'equity': {'Item Name': amount, ...}
                }
        """
        financial_data = {
            'assets': {},
            'liabilities': {},
            'equity': {}
        }
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                
                # Extract assets
                assets_section = self._extract_section(text, "ASSETS", "LIABILITIES")
                financial_data['assets'].update(self._parse_financial_items(assets_section))
                
                # Extract liabilities
                liabilities_section = self._extract_section(text, "LIABILITIES", "EQUITY")
                financial_data['liabilities'].update(self._parse_financial_items(liabilities_section))
                
                # Extract equity
                equity_section = self._extract_section(text, "EQUITY", "TOTAL LIABILITIES")
                financial_data['equity'].update(self._parse_financial_items(equity_section))
        
        return financial_data
    
    def _extract_generic_financial_data(self) -> Dict[str, Dict[str, float]]:
        """
        Fallback method for unknown statement types (private method).
        
        Returns a minimal structure when the statement type cannot be determined.
        
        Returns:
            Dict[str, Dict[str, float]]: Minimal structure with empty unknown_data category.
        """
        return {"unknown_data": {}}
    
    def _extract_section(self, text: str, start_marker: str, end_marker: str) -> str:
        """
        Extract text between two marker strings (private method).
        
        Utility method to isolate specific sections of the financial statement
        for targeted parsing.
        
        Args:
            text (str): Full text to search within.
            start_marker (str): Text marking the beginning of the section.
            end_marker (str): Text marking the end of the section.
        
        Returns:
            str: Text between the markers, or from start_marker to end if end_marker not found.
                 Returns empty string if start_marker not found or on error.
        """
        try:
            start_idx = text.find(start_marker)
            end_idx = text.find(end_marker, start_idx)
            if start_idx != -1 and end_idx != -1:
                return text[start_idx:end_idx]
            elif start_idx != -1:
                return text[start_idx:]
            return ""
        except:
            return ""
    
    def _parse_financial_items(self, section_text: str) -> Dict[str, float]:
        """
        Parse simple financial line items from a text section (private method).
        
        Extracts line items in the format "Item Name    Amount" used in balance sheets.
        Handles negative amounts and cleans up item names.
        
        Args:
            section_text (str): Text section containing line items to parse.
        
        Returns:
            Dict[str, float]: Dictionary mapping item names to amounts.
        
        Note:
            - Handles negative amounts (indicated by trailing '-')
            - Cleans up item names by removing prefixes like "Cash--" or "Less "
            - Skips lines that don't match the expected pattern
        """
        items = {}
        lines = section_text.split('\n')
        
        for line in lines:
            # Look for lines with financial amounts
            # Pattern: text followed by amount (with commas and decimals)
            match = re.search(r'(.+?)\s+([\d,]+\.?\d*)-?$', line.strip())
            if match:
                item_name = match.group(1).strip()
                amount_str = match.group(2).replace(',', '')
                
                try:
                    # Handle negative amounts (ending with -)
                    if line.strip().endswith('-'):
                        amount = -float(amount_str)
                    else:
                        amount = float(amount_str)
                    
                    # Clean up item names
                    item_name = re.sub(r'^(Cash--|Less\s+)', '', item_name)
                    items[item_name] = amount
                except ValueError:
                    continue
        
        return items
    
    def extract_with_coordinates(self) -> List[Dict]:
        """
        Extract text with position coordinates for advanced processing.
        
        Extracts individual characters with their precise position coordinates,
        useful for advanced layout analysis or custom parsing logic.
        
        Returns:
            List[Dict]: List of character objects with structure:
                [
                    {
                        'page': int, 'text': str, 'x0': float, 'y0': float,
                        'x1': float, 'y1': float, 'size': float
                    }, ...
                ]
        
        Note:
            - Coordinates are in PDF coordinate system (bottom-left origin)
            - x0,y0 = bottom-left corner, x1,y1 = top-right corner of character
            - size = font size of the character
        """
        text_objects = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                chars = page.chars
                for char in chars:
                    text_objects.append({
                        'page': page_num + 1,
                        'text': char['text'],
                        'x0': char['x0'],
                        'y0': char['y0'],
                        'x1': char['x1'],
                        'y1': char['y1'],
                        'size': char['size']
                    })
        
        return text_objects
    
    def export_to_dataframes(self) -> Dict[str, pd.DataFrame]:
        """
        Export financial data to pandas DataFrames for analysis.
        
        Converts the extracted financial data into structured DataFrames with
        calculated metrics. The DataFrame structure depends on the statement type.
        
        Returns:
            Dict[str, pd.DataFrame]: Dictionary containing DataFrames:
                - 'operating_results': Budget vs actual data with variance percentages
                - 'branch_breakdown': Branch data with percentage calculations
                - 'balance_sheet': Simple item-amount structure
        
        DataFrame Columns:
            Operating Results:
                category, line_item, march_actual, march_budget, march_variance,
                ytd_actual, ytd_budget, ytd_variance, march_variance_pct, ytd_variance_pct
            
            Branch Breakdown:
                category, line_item, armp_total, army, navy, usmc,
                army_pct, navy_pct, usmc_pct
            
            Balance Sheet:
                category, item, amount
        """
        statement_type = self.detect_statement_type()
        financial_data = self.extract_financial_data()
        dataframes = {}
        
        if statement_type == "operating_results":
            # Create operating results DataFrame
            all_items = []
            for category, items in financial_data.items():
                for item_name, values in items.items():
                    if isinstance(values, dict):
                        row = {
                            'category': category,
                            'line_item': item_name,
                            'march_actual': values.get('march_actual', 0),
                            'march_budget': values.get('march_budget', 0),
                            'march_variance': values.get('march_variance', 0),
                            'ytd_actual': values.get('ytd_actual', 0),
                            'ytd_budget': values.get('ytd_budget', 0),
                            'ytd_variance': values.get('ytd_variance', 0)
                        }
                        # Calculate variance percentages
                        row['march_variance_pct'] = (row['march_variance'] / row['march_budget'] * 100) if row['march_budget'] != 0 else 0
                        row['ytd_variance_pct'] = (row['ytd_variance'] / row['ytd_budget'] * 100) if row['ytd_budget'] != 0 else 0
                        all_items.append(row)
            
            dataframes['operating_results'] = pd.DataFrame(all_items)
            
        elif statement_type == "branch_breakdown":
            # Create branch breakdown DataFrame
            all_items = []
            for category, items in financial_data.items():
                for item_name, values in items.items():
                    if isinstance(values, dict):
                        row = {
                            'category': category,
                            'line_item': item_name,
                            'armp_total': values.get('armp_total', 0),
                            'army': values.get('army', 0),
                            'navy': values.get('navy', 0),
                            'usmc': values.get('usmc', 0)
                        }
                        # Calculate branch percentages
                        total = row['armp_total']
                        if total != 0:
                            row['army_pct'] = (row['army'] / total * 100)
                            row['navy_pct'] = (row['navy'] / total * 100)
                            row['usmc_pct'] = (row['usmc'] / total * 100)
                        else:
                            row['army_pct'] = row['navy_pct'] = row['usmc_pct'] = 0
                        
                        all_items.append(row)
            
            dataframes['branch_breakdown'] = pd.DataFrame(all_items)
            
        else:
            # Create balance sheet DataFrame (original logic)
            all_items = []
            for category, items in financial_data.items():
                for item, amount in items.items():
                    all_items.append({
                        'category': category,
                        'item': item,
                        'amount': amount
                    })
            dataframes['balance_sheet'] = pd.DataFrame(all_items)
        
        return dataframes
    
    def generate_operating_summary_report(self, operating_data: Dict) -> str:
        """
        Generate a formatted summary report for operating results data.
        
        Creates a human-readable text report highlighting key performance indicators,
        revenue performance, and top expense variances from operating results data.
        
        Args:
            operating_data (Dict): Operating results data from extract_operating_results().
        
        Returns:
            str: Formatted text report with sections for:
                - Key Performance Indicators (YTD Net Revenue, Budget, Variance)
                - Revenue Performance (by line item with variance percentages)
                - Top 5 Expense Variances (sorted by absolute variance percentage)
        
        Example:
            >>> extractor = FinancialStatementExtractor("operating_statement.pdf")
            >>> data = extractor.extract_operating_results()
            >>> report = extractor.generate_operating_summary_report(data)
            >>> print(report)
        """
        report = "OPERATING RESULTS SUMMARY\n"
        report += "=" * 50 + "\n\n"
        
        # Key Performance Indicators
        if 'net_revenue' in operating_data and 'Net Revenue' in operating_data['net_revenue']:
            net_rev = operating_data['net_revenue']['Net Revenue']
            report += "KEY PERFORMANCE INDICATORS:\n"
            report += f"  YTD Net Revenue: ${net_rev.get('ytd_actual', 0):,.2f}\n"
            report += f"  YTD Budget: ${net_rev.get('ytd_budget', 0):,.2f}\n"
            report += f"  YTD Variance: ${net_rev.get('ytd_variance', 0):,.2f}\n\n"
        
        # Revenue Analysis
        if 'revenue' in operating_data:
            report += "REVENUE PERFORMANCE:\n"
            for item, values in operating_data['revenue'].items():
                if isinstance(values, dict):
                    ytd_actual = values.get('ytd_actual', 0)
                    ytd_budget = values.get('ytd_budget', 0)
                    variance_pct = (values.get('ytd_variance', 0) / ytd_budget * 100) if ytd_budget != 0 else 0
                    report += f"  {item}:\n"
                    report += f"    YTD Actual: ${ytd_actual:,.2f}\n"
                    report += f"    YTD Budget: ${ytd_budget:,.2f}\n"
                    report += f"    Variance: {variance_pct:+.1f}%\n\n"
        
        # Expense Analysis - Top variances
        if 'operating_expenses' in operating_data:
            report += "TOP EXPENSE VARIANCES (YTD):\n"
            expense_variances = []
            for item, values in operating_data['operating_expenses'].items():
                if isinstance(values, dict) and values.get('ytd_budget', 0) != 0:
                    variance_pct = values.get('ytd_variance', 0) / values.get('ytd_budget', 1) * 100
                    expense_variances.append((item, variance_pct, values.get('ytd_variance', 0)))
            
            # Sort by absolute variance percentage
            expense_variances.sort(key=lambda x: abs(x[1]), reverse=True)
            
            for item, variance_pct, variance_amount in expense_variances[:5]:
                report += f"  {item}: {variance_pct:+.1f}% (${variance_amount:+,.2f})\n"
        
        return report
    def generate_branch_summary_report(self, branch_data: Dict) -> str:
        """
        Generate a formatted summary report for branch breakdown data.
        
        Creates a human-readable text report showing revenue distribution, operating income,
        and profit margins across military branches (Army, Navy, USMC).
        
        Args:
            branch_data (Dict): Branch breakdown data from extract_branch_breakdown().
        
        Returns:
            str: Formatted text report with sections for:
                - Revenue by Branch (amounts and percentages)
                - Operating Income by Branch
                - Operating Margins by Branch (calculated percentages)
        
        Example:
            >>> extractor = FinancialStatementExtractor("branch_statement.pdf")
            >>> data = extractor.extract_branch_breakdown()
            >>> report = extractor.generate_branch_summary_report(data)
            >>> print(report)
        """
        report = "BRANCH OF SERVICE PERFORMANCE SUMMARY\n"
        report += "=" * 55 + "\n\n"
        
        # Revenue breakdown
        if 'revenue' in branch_data:
            report += "REVENUE BY BRANCH:\n"
            for item, values in branch_data['revenue'].items():
                if isinstance(values, dict):
                    total = values.get('armp_total', 0)
                    army_pct = (values.get('army', 0) / total * 100) if total != 0 else 0
                    navy_pct = (values.get('navy', 0) / total * 100) if total != 0 else 0
                    usmc_pct = (values.get('usmc', 0) / total * 100) if total != 0 else 0
                    
                    report += f"  {item}: ${total:,.2f}\n"
                    report += f"    Army: ${values.get('army', 0):,.2f} ({army_pct:.1f}%)\n"
                    report += f"    Navy: ${values.get('navy', 0):,.2f} ({navy_pct:.1f}%)\n"
                    report += f"    USMC: ${values.get('usmc', 0):,.2f} ({usmc_pct:.1f}%)\n\n"
        
        # Operating performance by branch
        if 'net_operating_income' in branch_data:
            report += "OPERATING INCOME BY BRANCH:\n"
            net_ops = branch_data['net_operating_income'].get('Net Operating Income', {})
            if net_ops:
                report += f"  Total: ${net_ops.get('armp_total', 0):,.2f}\n"
                report += f"    Army: ${net_ops.get('army', 0):,.2f}\n"
                report += f"    Navy: ${net_ops.get('navy', 0):,.2f}\n"
                report += f"    USMC: ${net_ops.get('usmc', 0):,.2f}\n\n"
        
        # Calculate and show profit margins
        performance = self.calculate_branch_performance(branch_data)
        if 'Operating Margin' in performance:
            margins = performance['Operating Margin']
            report += "OPERATING MARGINS BY BRANCH:\n"
            report += f"  Army: {margins.get('army_margin_pct', 0):.1f}%\n"
            report += f"  Navy: {margins.get('navy_margin_pct', 0):.1f}%\n"
            report += f"  USMC: {margins.get('usmc_margin_pct', 0):.1f}%\n"
            report += f"  Overall: {margins.get('armp_margin_pct', 0):.1f}%\n\n"
        
        return report
    def generate_summary_report(self) -> str:
        """
        Generate an appropriate summary report based on the detected statement type.
        
        Automatically detects the statement type and generates the corresponding
        specialized summary report.
        
        Returns:
            str: Formatted text summary report. Type depends on detected statement:
                - Branch breakdown: Branch performance summary
                - Operating results: Operating results summary  
                - Balance sheet: Balance sheet summary
                - Unknown: Balance sheet summary (fallback)
        
        Example:
            >>> extractor = FinancialStatementExtractor("statement.pdf")
            >>> summary = extractor.generate_summary_report()
            >>> print(summary)
        """
        statement_type = self.detect_statement_type()
        financial_data = self.extract_financial_data()
        
        if statement_type == "branch_breakdown":
            return self.generate_branch_summary_report(financial_data)
        elif statement_type == "operating_results":
            return self.generate_operating_summary_report(financial_data)
        else:
            return self.generate_balance_sheet_summary_report(financial_data)
    
    def generate_balance_sheet_summary_report(self, financial_data: Dict) -> str:
        """
        Generate a formatted summary report for balance sheet data.
        
        Creates a human-readable text report showing assets, liabilities, and equity
        with totals for each category.
        
        Args:
            financial_data (Dict): Balance sheet data from _extract_balance_sheet_data().
        
        Returns:
            str: Formatted text report with sections for each category (assets, 
                 liabilities, equity) showing individual items and category totals.
        
        Example:
            >>> extractor = FinancialStatementExtractor("balance_sheet.pdf")
            >>> data = extractor._extract_balance_sheet_data()
            >>> report = extractor.generate_balance_sheet_summary_report(data)
            >>> print(report)
        """
        report = "FINANCIAL STATEMENT SUMMARY\n"
        report += "=" * 40 + "\n\n"
        
        for category, items in financial_data.items():
            if items:
                report += f"{category.upper()}:\n"
                total = 0
                for item, amount in items.items():
                    report += f"  {item}: ${amount:,.2f}\n"
                    total += amount
                report += f"  TOTAL {category.upper()}: ${total:,.2f}\n\n"
        
        return report

def format_report_df(extractor):
    """
    Format a comprehensive report dictionary from a FinancialStatementExtractor instance.
    
    Extracts all available data and formats it into a structured dictionary containing
    raw text, tables, financial data, summary report, and DataFrames.
    
    Args:
        extractor (FinancialStatementExtractor): Initialized extractor instance.
    
    Returns:
        Dict: Comprehensive report dictionary with keys:
            - "full_text": Complete PDF text content
            - "tables": List of extracted DataFrames from tables
            - "financial_data": Structured financial data dictionary
            - "summary_report": Formatted text summary report
            - "dataframes": Dictionary of analysis-ready DataFrames
    
    Example:
        >>> extractor = FinancialStatementExtractor("statement.pdf")
        >>> report = format_report_df(extractor)
        >>> print(report.keys())
        dict_keys(['full_text', 'tables', 'financial_data', 'summary_report', 'dataframes'])
    """
    report = dict()
    
    full_text = extractor.extract_all_text()
    report["full_text"] = full_text
    
    tables = extractor.extract_tables()
    report["tables"] = tables
    
    financial_data = extractor.extract_financial_data()
    report["financial_data"] = financial_data
    
    summary_report = extractor.generate_summary_report()
    report["summary_report"] = summary_report
    
    dataframes = extractor.export_to_dataframes()
    report["dataframes"] = dataframes
    
    return report

def output_report(report_df, output_dir, page_num=None):
    """
    Output report DataFrames to CSV files in the specified directory.
    
    Saves all DataFrames from the report dictionary as CSV files with appropriate
    naming conventions based on whether a page number is provided.
    
    Args:
        report_df (Dict): Report dictionary from format_report_df() containing "dataframes" key.
        output_dir (str): Directory path where CSV files will be saved.
        page_num (int, optional): Page number for file naming. If provided, files are named
                                 "page_{page_num:03}_{df_name}.csv". Otherwise, 
                                 "{df_name}_data.csv".
    
    Side Effects:
        - Creates CSV files in the output directory
        - Prints confirmation messages for each saved file
        - Creates directories if they don't exist (via pandas to_csv)
    
    Example:
        >>> extractor = FinancialStatementExtractor("statement.pdf")
        >>> report = format_report_df(extractor)
        >>> output_report(report, "/output/dir", page_num=1)
        Saved /output/dir/page_001_operating_results.csv
    """
    for df_name, df in report_df["dataframes"].items():        
        if page_num:
            output_file = f"{output_dir}/page_{page_num:03}_{df_name}.csv"
        else:
            output_file = f"{output_dir}/{df_name}_data.csv"
        df.to_csv(output_file, index=False)
        print(f"Saved {output_file}")

if __name__ == "__main__":
    for i in range(712):
        page_num = i + 1
        print(f"page_num: {page_num:03}")
        source_pdf_base_path = "/Users/brentbrewington/Downloads/Data/Financial Statements_page_"
        extractor = FinancialStatementExtractor(f"{source_pdf_base_path}{page_num:03}.pdf")
        report = format_report_df(extractor)
        output_report(report, page_num=page_num)
        del extractor
