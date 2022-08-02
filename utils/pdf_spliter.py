from PyPDF2 import PdfFileWriter, PdfFileReader
import re
from tqdm.notebook import tqdm
import os 

class PDFSpliter:
    def __init__(self):
        self.pdf = None
        self.abstract_pages = []
        self.abstract_pages_filtered = []  # remove papers with only 1 pages
        self.list_ranges = []

    def read_pdf(self, pdf_path):
        self.pdf = PdfFileReader(open(pdf_path, "rb"))

    def get_abstract_pages(self):
        '''
        get page numbers having abstract
        '''
        for i in tqdm(range(self.pdf.numPages)):
            output = PdfFileWriter()
            output.addPage(self.pdf.getPage(i))

            page = output.pages[0]
            text = page.extract_text()

            if re.findall('abstract:|abstract\n', text, re.I):
                self.abstract_pages.append(i + 1)

    def filter_abstract_pages(self):
        '''
        remove papers with only 1 pages
        '''

        for idx, page in enumerate(self.abstract_pages[:-1]):
            if page == self.abstract_pages[idx + 1] + 1:
                pass
            else:
                self.abstract_pages_filtered.append(page)
        self.abstract_pages_filtered.append(page + 1)
        print(f'len abstract pages : {len(self.abstract_pages)} -- len filtered : {len(self.abstract_pages_filtered)}')

    def get_ranges(self):
        '''
        range of pages of each article
        '''
        for idx, elt in enumerate(self.abstract_pages_filtered[:-1]):
            self.list_ranges.append((elt, self.abstract_pages_filtered[idx + 1] - 1))

    def output_range(self, range_pages: tuple, file_name: str, output_dir=''):
        '''
        output range of pages in pdf doc
        '''
        p1, p2 = range_pages
        output = PdfFileWriter()

        for page in range(p1 - 1, p2):
            page = self.pdf.getPage(page)
            text = page.extract_text()

            if len(text.split()) > 20:
                output.addPage(page)

        output_path = os.path.join(output_dir, f"{file_name}_{p1}_{p2 + 1}.pdf")
        with open(output_path, "wb") as outputStream:
            output.write(outputStream)

    def split(self, pdf_path, output_dir=''):
        '''
        split pdf_path
        '''
        self.read_pdf(pdf_path)
        print('>> Getting pdf pages..')
        self.get_abstract_pages()

        print('>> Filtering..')
        self.filter_abstract_pages()

        print('>> Get ranges..')
        self.get_ranges()

        print('>> Exporting..')
        file_name = pdf_path.split('/')[-1]

        for range_pages in tqdm(self.list_ranges):
            self.output_range(range_pages, file_name, output_dir)