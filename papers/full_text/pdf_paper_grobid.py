from naimai.papers.raw import papers, paper_full_base
from naimai.constants.regex import regex_paper_year
from naimai.constants.paths import path_open_citations
from naimai.utils.general import get_soup
from naimai.decorators import update_naimai_dois
from spacy_langdetect import LanguageDetector
from naimai.utils.regex import multiple_replace
from naimai.constants.nlp import nlp_vocab
from tqdm.notebook import tqdm
import spacy
import ast
import os
from bs4 import BeautifulSoup
import re

class paper_grobid(paper_full_base):
    def __init__(self,paper_path):
        super().__init__()
        self.database = 'pdf'
        self.xml_filename = paper_path
        self.xml_soup = None

    def read_file(self):
        xml_file = open(self.xml_filename, 'r')
        self.xml_soup = BeautifulSoup(xml_file, "lxml")

    def get_data(self,name,attrs={},findall=False,is_text=True):
        '''
        get data using name and attrs
        :param name:
        :param attrs:
        :param findall:
        :return:
        '''
        if findall:
            text = self.xml_soup.find_all(name=name, attrs=attrs)
            return text
        else:
            text = self.xml_soup.find(name=name, attrs=attrs)
            if text and is_text:
                return text.text
            else:
                return text

    def get_doi(self):
        name = 'idno'
        attrs = {'type': 'DOI'}
        self.doi= self.get_data(name=name,attrs=attrs)

    def get_Abstract(self):
        name = 'abstract'
        self.Abstract= self.get_data(name=name).replace('\n',' ').strip()

    def get_Keywords(self):
        name = 'keywords'
        kwords= self.get_data(name=name)
        kwords = re.sub('^\n','',kwords)
        kwords = re.sub('\n$','',kwords)
        self.Keywords = kwords.replace('\n',', ').strip()

    def get_Title(self):
        name='title'
        attrs = {'type':'main'}
        self.Title = self.get_data(name=name,attrs=attrs)

    def get_Authors(self):
        name = 'analytic'
        first = self.get_data(name=name, is_text=False)
        name = 'author'
        authors = first.find_all(name=name)
        self.Authors = ', '.join([elt.find(name="forename").text + ' ' + elt.find(name="surname").text for elt in authors])

    def get_year(self):
        name = 'date'
        attrs = {'type': "published"}
        date = self.get_data(name=name, attrs=attrs)
        year = re.findall(regex_paper_year, date)
        if year:
            self.year = year[0]

    def get_Journal(self):
        name='title'
        attrs = {'level': 'j'}
        self.Journal = self.get_data(name=name,attrs=attrs)

    def get_numCitedBy(self):
        if self.doi:
            path = path_open_citations + self.doi
            soup = get_soup(path)
            soup_list = ast.literal_eval(soup.text)
            if isinstance(soup_list,list):
                self.numCitedBy = len(soup_list)

    def replace_abbreviations(self):
        abbreviations_dict = self.get_abbreviations_dict()
        if abbreviations_dict:
            self.Abstract = multiple_replace(abbreviations_dict, self.Abstract)
            self.Title = multiple_replace(abbreviations_dict, self.Title)
            self.Keywords = multiple_replace(abbreviations_dict, self.Title)


class papers_grobid(papers):
    def __init__(self, papers_path,nlp=None):
        super().__init__() # loading self.naimai_dois & other attributes
        self.naimai_dois = []
        self.papers_path = papers_path
        self.list_files = [elt for elt in os.listdir(papers_path) if '.pdf' in elt]
        print('Len data : ', len(self.list_files))
        if nlp:
            self.nlp = nlp
        else:
            print('Loading nlp vocab..')
            self.nlp = spacy.load(nlp_vocab)
            self.nlp.add_pipe(LanguageDetector(), name='language_detector', last=True)

    def add_paper(self,paper_path):
            new_paper = paper_grobid(paper_path=paper_path)
            new_paper.get_doi()
            if not new_paper.is_in_database(self.naimai_dois):
                self.naimai_dois.append(new_paper.doi)
                new_paper.get_Title()
                if new_paper.is_paper_english(self.nlp):
                    new_paper.get_Authors()
                    new_paper.get_Journal()
                    new_paper.get_year()
                    new_paper.replace_abbreviations()
                    new_paper.get_numCitedBy()
                    self.elements[new_paper.doi] = new_paper.save_dict()



    # @update_naimai_dois
    def get_papers(self):
        for pdf in tqdm(self.list_files):
            path = os.path.join(self.papers_path,pdf)
            self.add_paper(paper_path = path)