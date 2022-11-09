from unittest import TestCase
from naimai.papers.raw import papers
import os

class papersTest(TestCase):
    '''
    Test case papers object, by testing if the correct files are read, the title, numcitedby, database and journal are correct for the first paper.
    '''
    @classmethod
    def setUpClass(cls) -> None:
        cls.fnames = ['10.21776/ub.jam.2020.018.04.02', '10.21776/ub.jam.2021.019.02.15', '10.21776/ub.jam.2017.015.02.06']
        cls.title = 'DETERMINANTS OF INTEREST IN USING TRAVEL VLOGS ON YOUTUBE AS A REFERENCE FOR TRAVELING'
        cls.numcitedby = 0.5
        cls.journal = 'Jurnal Aplikasi Manajemen                                Journal of Applied Management'
        cls.database = "doij"

        path = os.path.join('tests', 'papers', 'input_data', 'doij_input.csv')
        obj = papers(path, database="doij")
        obj.get_papers(update_dois=False, show_tqdm=False, check_database=False)
        result = obj.elements
        cls.keys = list(result.keys())
        cls.first_paper = result[cls.keys[0]]

    def test_fnames(self):
        '''
        test if correct fnames are read
        :return:
        '''
        self.assertEqual(self.keys, self.fnames)

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