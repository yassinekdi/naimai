from unittest import TestCase
from naimai.papers.full_text.pdf_paper import papers_pdf
from naimai.pipelines.producers import Custom_Producer
import os

class CustomProducerTest(TestCase):
    '''
    Test custom producer, by producing pdf papers.
    '''
    @classmethod
    def setUpClass(cls) -> None:
        cls.fnames = ['Bousmar1999.pdf_objectives', 'Bousmar1999.pdf_methods', 'Bousmar1999.pdf_results', 'Chen2016.pdf_objectives', 'Chen2016.pdf_methods', 'Chen2016.pdf_results']
        cls.fname_test = 'Chen2016.pdf_objectives'
        cls.title = 'Determination of Apparent Shear Stress and its Application in Compound Channels'
        cls.numcitedby = 10
        cls.journal = 'Procedia Engineering'
        cls.authors = 'Chen et al. (2016)'
        cls.first_message = 'The momentum exchange in the mixing zone of compound channel is a common phenomenon and has an important effect on discharge estimation.'
        cls.reported = 'Chen et al. (2016) quantified with apparent shear stress (ASS) at the interface of floodplain and main channel.'



        path = os.path.join('tests', 'papers', 'input_data')
        obj = papers_pdf(papers_path=path)
        obj.get_papers()

        producer = Custom_Producer(papers_dict=obj.elements)
        producer.produce_custom_papers(show_tqdm=False)

        result = producer.produced_custom_papers
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

    def test_authors(self):
        '''
        test authors of the first paper
        :return:
        '''
        authors_first_paper = self.first_paper['authors']
        self.assertEqual(authors_first_paper, self.authors)

    def test_first_msg(self):
        '''
        test first message of the first paper
        :return:
        '''
        message_first_paper = self.first_paper['messages']
        self.assertEqual(message_first_paper, self.first_message)

    def test_reported(self):
        '''
        test first message of the first paper
        :return:
        '''
        reported_first_paper = self.first_paper['reported']
        self.assertEqual(reported_first_paper, self.reported)