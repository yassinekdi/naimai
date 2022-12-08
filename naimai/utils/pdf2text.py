import re
from io import StringIO, BytesIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import pdf2image
import pytesseract
import unidecode


def convert_pdf_to_txt(obj,is_path=True,use_ocr=False):
    result = ''
    try:
        result=pm_convert_pdf_to_txt(obj,is_path=is_path)
        nb_new_lines = len(re.findall('\n[^.?]\n', result))
        if (nb_new_lines >5000) or nb_new_lines==0:
            result = ''
            if is_path:
                print('OCR TO USE in ', obj)
            else:
                print('OCR USED')
            if use_ocr:
                result = ocr_convert_pdf_to_txt(obj,is_path=is_path)

    except:
        if is_path:
            print('except OCR USED in ', obj)
        else:
            print('OCR USED')
        if use_ocr:
            result = ocr_convert_pdf_to_txt(obj,is_path=is_path)

    return result

def ocr_convert_pdf_to_txt(obj,is_path=True):
    if is_path:
        with open(obj, 'rb') as f:
            pdf_content = f.read()
    else:
        pdf_content = BytesIO(obj)

    doc = pdf2image.convert_from_bytes(pdf_content)
    article = []
    for page_data in doc:
        txt = pytesseract.image_to_string(page_data).encode("utf-8")
        article.append(txt.decode("utf-8"))
    text = " ".join(article)
    return unidecode.unidecode(text.replace('e´', 'é'))

def pm_convert_pdf_to_txt(obj, pages=None,is_path=True):
    if not pages:
        pagenums = set()
    else:
        pagenums = set(pages)
    output = StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)

    if is_path:
        infile = open(obj, 'rb')
    else:
        infile = BytesIO(obj)
    for page in PDFPage.get_pages(infile, pagenums):
        interpreter.process_page(page)
    infile.close()
    converter.close()
    text = output.getvalue()
    output.close()
    return unidecode.unidecode(text.replace('e´','é'))

def find_in_txt(original,lower_txt):
  idx1=original.lower().find(lower_txt)
  idxN = idx1 + len(lower_txt)
  return original[idx1:idxN]
