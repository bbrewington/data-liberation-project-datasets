from split_pdf import split_pdf
from financial_statement_extractor import FinancialStatementExtractor, format_report_df, output_report

START_PAGE = 1
END_PAGE = 10

def main(run_split=False):
    if run_split:
        split_pdf(
            # Financial Statements.pdf has 712 pages
            file_path="/Users/brentbrewington/Downloads/Data/Financial Statements.pdf",
            name_template="/Users/brentbrewington/Downloads/Data_temp/Financial Statements_page_{:03}.pdf"
        )
    
    for i in range(START_PAGE, END_PAGE + 1):
        page_num = i
        print(f"page_num: {page_num:03}")
        source_pdf_base_path = "/Users/brentbrewington/Downloads/Data/Financial Statements_page_"
        extractor = FinancialStatementExtractor(f"{source_pdf_base_path}{page_num:03}.pdf")
        report = format_report_df(extractor)
        output_report(report, output_dir="data_need_to_qa", page_num=page_num)
        del extractor

if __name__ == "__main__":
    main()

