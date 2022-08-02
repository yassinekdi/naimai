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

from spacy.language import Language

def create_lang_detector(nlp, name):
    return LanguageDetector()


class paper_grobid(paper_full_base):
    def __init__(self,paper_path='',paper_xml=''):
        super().__init__()
        self.database = 'pdf'
        self.xml_data = paper_xml
        self.xml_soup = None


        if paper_path:
            self.read_file(paper_path,is_path=True)
        else:
            self.read_file(paper_xml, is_path=False)

    def read_file(self,xml,is_path):
        if is_path:
            xml_file = open(xml, 'r')
        else:
            xml_file = xml
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
            if text:
              return text[0]
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
        if not self.doi:
            self.database = 'mine'

    def get_Abstract(self):
        name = 'abstract'
        self.Abstract= self.get_data(name=name).replace('\n',' ').strip()

    def get_Keywords(self):
        name = 'keywords'
        kwords= self.get_data(name=name)
        if kwords:
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
        result = []
        for elt in authors:
            try:
                fname = elt.find(name="forename").text
                lname = elt.find(name="surname").text
                result.append(fname + ' ' + lname)
            except:
                pass
        if result:
            self.Authors = ', '.join(result)
        else:
            self.Authors = ''

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
    def __init__(self, papers_path='',papers_dict={},nlp=None):
        super().__init__() # loading self.naimai_dois & other attributes
        self.naimai_dois = []
        self.papers_path = papers_path
        self.papers_dict = {}
        if papers_path:
            self.list_files = [elt for elt in os.listdir(papers_path) if '.pdf' in elt]
        else:
            self.list_files = list(papers_dict)
            self.papers_dict = papers_dict
        print('Len data : ', len(self.list_files))
        if nlp:
            self.nlp = nlp
        else:
            print('Loading nlp vocab..')
            self.nlp = spacy.load(nlp_vocab)
            Language.factory("language_detector", func=create_lang_detector)
            self.nlp.add_pipe('language_detector', last=True)

    def add_paper(self,paper_path='',paper_xml=''):
            if paper_path:
                new_paper = paper_grobid(paper_path=paper_path)
            else:
                new_paper = paper_grobid(paper_xml=paper_xml)
            new_paper.get_doi()
            # if not new_paper.is_in_database(self.naimai_dois):
            new_paper.get_Title()
            if new_paper.is_paper_english(self.nlp):
                new_paper.get_Abstract()
                if len(new_paper.Abstract.split()) > 5:
                    new_paper.get_Journal()
                    new_paper.get_Authors()
                    new_paper.get_year()
                    new_paper.get_Keywords()
                    new_paper.replace_abbreviations()
                    new_paper.get_numCitedBy()
                    if new_paper.doi:
                        self.elements[new_paper.doi] = new_paper.save_dict()
                        self.naimai_dois.append(new_paper.doi)
                    else:
                        self.elements[new_paper.Title] = new_paper.save_dict()


    def get_papers(self,idx_start=0,idx_finish=-1):
        if idx_finish==-1:
            list_files = self.list_files[idx_start:]
        else:
            list_files = self.list_files[idx_start:idx_finish]

        for pdf in tqdm(list_files):
            if self.papers_path:
                path = os.path.join(self.papers_path,pdf)
                self.add_paper(paper_path=path)
            else:
                paper_xml = self.papers_dict[pdf]
                self.add_paper(paper_xml=paper_xml)

