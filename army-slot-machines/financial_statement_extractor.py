import pdfplumber
import pandas as pd
import re
from typing import Dict, List

class FinancialStatementExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pages_data = []
        self.statement_type = None  # Will be detected automatically
    
    def extract_all_text(self) -> str:
        """Extract all text from PDF"""
        full_text = ""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
        return full_text
    
    def extract_tables(self) -> List[pd.DataFrame]:
        """Extract tables from PDF"""
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
        """Detect the type of financial statement"""
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
        """Extract budget vs actual operating results data"""
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
        """Parse line items with March Actual, March Budget, YTD Actual, YTD Budget columns"""
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
        """Extract a single summary line with budget vs actual data"""
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
    
    def calculate_variance_analysis(self, operating_data: Dict) -> Dict[str, Dict[str, float]]:
        """Calculate variance analysis percentages"""
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
        
    def extract_branch_breakdown(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        """Extract branch of service breakdown data"""
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
        """Parse line items with ARMP Total, Army, Navy, USMC columns"""
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
        """Extract a single summary line with branch breakdown"""
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
        """Calculate branch performance metrics and percentages"""
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
        """Calculate variance analysis percentages"""
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
        """Extract structured financial data - detects statement type automatically"""
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
        """Extract balance sheet data (original method)"""
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
        """Fallback method for unknown statement types"""
        return {"unknown_data": {}}
    
    def _extract_section(self, text: str, start_marker: str, end_marker: str) -> str:
        """Extract text between two markers"""
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
        """Parse financial line items from a section"""
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
        """Extract text with position coordinates for advanced processing"""
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
        """Export financial data to DataFrames for analysis"""
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
        """Generate a summary report for operating results"""
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
        """Generate a summary report for branch breakdown"""
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
        """Generate appropriate summary report based on statement type"""
        statement_type = self.detect_statement_type()
        financial_data = self.extract_financial_data()
        
        if statement_type == "branch_breakdown":
            return self.generate_branch_summary_report(financial_data)
        elif statement_type == "operating_results":
            return self.generate_operating_summary_report(financial_data)
        else:
            return self.generate_balance_sheet_summary_report(financial_data)
    
    def generate_balance_sheet_summary_report(self, financial_data: Dict) -> str:
        """Generate a summary report of the balance sheet (original method)"""
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
