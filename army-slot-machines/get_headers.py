import pdfplumber
from typing import List, TypedDict
import pandas as pd

class FileMeta(TypedDict):
    file_path: str
    header_items: List[str]

def extract_headers_from_pdf(pdf_path: str, n_lines: int = 4) -> List[FileMeta]:
    """Extract the first n_lines of text from each page in the PDF."""
    page_meta_list: List[FileMeta] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            print(page_num)
            text = page.extract_text() or ""
            header_items = text.split("\n")[:n_lines]
            page_meta_list.append({
                "file_path": f"{pdf_path}",
                "page": page_num,
                "header_items": header_items
            })
    return page_meta_list

pdf_path = "/Users/brentbrewington/Downloads/Data/Financial Statements.pdf"
page_meta_list = extract_headers_from_pdf(pdf_path)

# Example: preview first 3 pages
for meta in page_meta_list[:3]:
    print(meta)

df = pd.DataFrame(page_meta_list)
df2 = df.copy()
df2[['header_1', 'header_2', 'header_3', 'header_4']] = pd.DataFrame(df2.header_items.tolist(), index= df2.index)
df2.to_csv('page_metadata.csv')
