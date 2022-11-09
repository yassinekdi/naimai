from unittest import TestCase
from naimai.papers.only_abstracts.issn import papers_issn
import os

class papers_issnTest(TestCase):
    '''
    Test case papers issn object, by testing if the correct files are read, the title, numcitedby, database and journal are correct for the first paper.
    '''
    @classmethod
    def setUpClass(cls) -> None:
        cls.fnames = ['10.3390/agriculture10020049', '10.3390/agriculture11080782', '10.3390/agriculture10060225']
        cls.title = 'Marketable Yield of Potato and Its Quantitative Parameters after Application of Herbicides and Biostimulants'
        cls.numcitedby = float(7)
        cls.journal = 'Agriculture'
        cls.database = "issn"

        path = os.path.join('tests', 'papers', 'input_data', 'issn_input.csv')
        obj = papers_issn(path, database="issn")
        obj.get_papers(update_dois=False, show_tqdm=False, check_database=False)
        result = obj.elements
        cls.keys=list(result.keys())
        cls.first_paper = result[cls.keys[0]]

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