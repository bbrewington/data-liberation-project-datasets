import pymupdf

def split_pdf(file_path, name_template):
    doc = pymupdf.open(file_path)
    for i in range(len(doc)):
        page_doc = pymupdf.open()
        page_doc.insert_pdf(doc, from_page=i, to_page=i)
        page_doc.save(name_template.format(i + 1))
        page_doc.close()
    doc.close()
