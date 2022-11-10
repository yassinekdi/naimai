'''
Extract data from an article in PDF using grobid package modified for naimai.
The modified grobid package is in the grobid file.
'''

from naimai.models.abbreviation import extract_abbreviation_definition_pairs
from naimai.constants.regex import regex_paper_year
from naimai.constants.paths import path_open_citations, grobid_url
from naimai.papers.full_text.grobid.pdf2dict import GrobidClient
from naimai.utils.general import get_soup
from naimai.utils.regex import multiple_replace
from tqdm.notebook import tqdm
from bs4 import BeautifulSoup
import ast
import os
import re

class paper_pdf:
    def __init__(self,fname,pdf_content):
        self.database = 'pdf'
        self.fname = fname
        self.content = BeautifulSoup(pdf_content, "lxml")
        self.numCitedBy = .5
        self.Journal = ''
        self.Abstract = ''
        self.Authors = ''
        self.doi = ''
        self.year = 999
        self.Title = ''

        # if paper_path:
        #     self.read_xml_file(paper_path, is_path=True)
        # else:
        #     self.read_xml_file(paper_xml, is_path=False)

    # def read_xml_file(self, xml, is_path):
    #     '''
    #     read xml file (converted using grobid)
    #     :param xml:
    #     :param is_path:
    #     :return:
    #     '''
    #     if is_path:
    #         xml_file = open(xml, 'r')
    #     else:
    #         xml_file = xml
    #     self.xml_soup = BeautifulSoup(xml_file, "lxml")


    def get_data(self,name,attrs={},findall=False,is_text=True):
        '''
        get data using name and attrs
        :param name:
        :param attrs:
        :param findall:
        :return:
        '''
        if findall:
            # text = self.xml_soup.find_all(name=name, attrs=attrs)
            text = self.content.find_all(name=name, attrs=attrs)
            if text:
              return text[0]
        else:
            # text = self.xml_soup.find(name=name, attrs=attrs)
            text = self.content.find(name=name, attrs=attrs)
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
        if date:
            year = re.findall(regex_paper_year, date)
            if year:
                self.year = year[0]
        else:
            self.year = ''

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

    def get_abbreviations_dict(self) -> dict:
        '''
        Get abbreviations and their meanings from the title and the abstract in a dictionary.
        Modified code from : https://gist.github.com/ijmarshall/b3d1de6ccf4fb8b5ee53
        :return:
        '''
        abstract_abbrevs = extract_abbreviation_definition_pairs(doc_text=self.Abstract)
        corrected_abbrevs = {}
        for k in abstract_abbrevs:
            corrected_abbrevs[' ' + k] = ' ' + abstract_abbrevs[k] + ' ' + '(' + k + ')'
        return corrected_abbrevs

    def replace_abbreviations(self):
        abbreviations_dict = self.get_abbreviations_dict()
        if abbreviations_dict:
            self.Abstract = multiple_replace(abbreviations_dict, self.Abstract)

    def save_dict(self) -> dict:
        '''
        Format the read data of the paper into a dictionary
        :return:
        '''
        attr_to_save = ['doi', 'Authors', 'year', 'database', 'Abstract', 'Title', 'numCitedBy',
                        'Journal']
        paper_to_save = {key: self.__dict__[key] for key in attr_to_save}
        return paper_to_save

class papers_pdf:
    def __init__(self, papers_path):
        '''
        process papers read with grobid
        :param database: name of database used
        :param papers_path:
        :param papers_dict:
        :param nlp:
        '''
        # super().__init__(papers_path, database, nlp)
        self.papers_path = papers_path
        self.elements = {}
        # if papers_path:
        #     self.list_files = [elt for elt in os.listdir(papers_path) if '.xml' in elt]
        # else:
        #     self.list_files = list(papers_dict)
        #     self.papers_dict = papers_dict
        self.list_files = [elt for elt in os.listdir(papers_path) if elt.endswith('.pdf')]
        print('Len data : ', len(self.list_files))

    def read_content(self):
        '''

        :return:
        '''
        pdf_files = [elt for elt in os.listdir(self.papers_path) if elt.endswith('.pdf')]
        data_dict = {}

        for fname in pdf_files:
            path = os.path.join(self.papers_path, fname)
            with open(path, "rb") as f:
                data_dict[fname] = f.read()
        client = GrobidClient(url=grobid_url)
        results = client.process("processHeaderDocument", input_path=data_dict)

        return results

    def add_paper(self,fname,pdf_content):
        new_paper = paper_pdf(fname=fname,pdf_content=pdf_content)
        # if paper_path:
        #     new_paper = paper_pdf(paper_path=paper_path)
        # else:
        #     new_paper = paper_pdf(paper_xml=paper_xml)
        new_paper.get_doi()
        new_paper.get_Title()
        new_paper.get_Abstract()
        if len(new_paper.Abstract.split()) > 5:
            new_paper.get_Journal()
            new_paper.get_Authors()
            new_paper.get_year()
            new_paper.get_Keywords()
            new_paper.replace_abbreviations()
            new_paper.get_numCitedBy()
            self.elements[fname] = new_paper.save_dict()

    def get_papers(self):
        data = self.read_content()

        for fname in tqdm(data):
            self.add_paper(fname=fname,pdf_content=data[fname])

