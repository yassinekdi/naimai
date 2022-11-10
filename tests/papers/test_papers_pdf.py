from unittest import TestCase
from naimai.papers.full_text.pdf_paper import papers_pdf
import os

class papers_pdfTest(TestCase):
    '''
    Test case papers issn object, by testing if the correct files are read, the title, numcitedby, database and journal are correct for the first paper.
    '''
    @classmethod
    def setUpClass(cls) -> None:
        cls.fnames = ['Bousmar1999.pdf', 'Chen2016.pdf']
        cls.title = 'Determination of Apparent Shear Stress and its Application in Compound Channels'
        cls.numcitedby = float(10)
        cls.journal = 'Procedia Engineering'
        cls.database = "pdf"

        pdfs_path = os.path.join('tests', 'papers', 'input_data')
        obj = papers_pdf(papers_path=pdfs_path)
        obj.get_papers()
        result = obj.elements
        cls.keys=list(result.keys())
        cls.first_paper = result[cls.keys[1]]

    def test_fnames(self):
        '''
        test if correct fnames are read
        :return:
        '''
        self.assertEqual(self.keys,self.fnames)

    def test_title(self):
        '''
        test title of the first paper
        :return:
        '''
        title_first_paper = self.first_paper['Title']
        self.assertEqual(title_first_paper, self.title)

    def test_numcitedby(self):
        '''
        test numcitedby of the first paper
        :return:
        '''
        numcitedby_first_paper = self.first_paper['numCitedBy']
        self.assertEqual(numcitedby_first_paper, self.numcitedby)

    def test_journal(self):
        '''
        test journal of the first paper
        :return:
        '''
        journal_first_paper = self.first_paper['Journal']
        self.assertEqual(journal_first_paper, self.journal)

    def test_database(self):
        '''
        test database of the first paper
        :return:
        '''
        database_first_paper = self.first_paper['database']
        self.assertEqual(database_first_paper, self.database)