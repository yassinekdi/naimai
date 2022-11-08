from unittest import TestCase
from naimai.papers.only_abstracts.egu import papers_egu
import os

class papers_eguTest(TestCase):
    '''
    Test case papers egu object, by testing if the correct files are read, the title, numcitedby, database and journal are correct for the first paper.
    '''
    @classmethod
    def setUpClass(cls) -> None:
        cls.fnames = ['10.5194/acp-22-9617-2022', '10.5194/acp-22-6625-2022', '10.5194/acp-22-4615-2022']
        cls.title = 'Quantifying methane emissions from the global scale down to point sources using satellite observations of atmospheric methane'
        cls.numcitedby = float(3)
        cls.journal = 'Atmospheric Chemistry and Physics'
        cls.database = "egu"

        path = os.path.join('naimai', 'tests', 'papers', 'input_data', 'egu_input.csv')
        obj = papers_egu(path, database="egu")
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