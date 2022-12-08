''' 
- paper_base Class: used extract data about a paper and format it as a dictionary. Each paper data is contained in a
 row of a csv file. The data are: :  doi, fields, abstract, title, authors, year of publication, journal, num of papers
 that cited the papers (numCitedBy).

- papers Class: used to format the input csv file that contains data about many papers. Each paper is formatted using
  the paper_bass class. In case a meta data needs to be overwritten, a new 'paper' and 'papers' class can be implemented, that inherits from
  paper_base and papers, as in the files in papers/only_abstracts/.

- paper_full_base Class [Not Finished]: class used to extract data from all
the article (instead of only the abstract, as in paper_base). 
'''

import random
import os
from naimai.utils.general import load_gzip, save_gzip
from naimai.constants.paths import naimai_dois_path
from naimai.models.abbreviation import extract_abbreviation_definition_pairs
# from naimai.processing import TextCleaner
from tqdm.notebook import tqdm
import pandas as pd
import numpy as np
from ast import literal_eval
import spacy
from naimai.constants.paths import path_open_citations
from naimai.utils.general import get_soup
from naimai.constants.nlp import nlp_vocab

from naimai.utils.regex import multiple_replace
from naimai.decorators import update_naimai_dois

from spacy.language import Language
from spacy_langdetect import LanguageDetector


def create_lang_detector(nlp, name):
    return LanguageDetector()

class paper_base:
    '''
    Paper class that map a row if the csv file with data about papers to a dictionary.
    '''
    def __init__(self,df: pd.DataFrame,idx_in_df: int):
        '''
        :param df: dataframe of the csv file with many papers data
        :param idx_in_df: index of row in df containing a paper data
        '''
        self.database=''
        self.file_name = idx_in_df
        self.paper_infos = df.iloc[idx_in_df,:]
        self.raw_text = ''
        self.fields = []
        self.numCitedBy = .5
        self.Introduction = ''
        self.Journal = ''
        self.highlights = []
        self.Abstract = ''
        self.Conclusion = ''
        self.Keywords = ''
        self.Authors = ''
        self.Title = ''
        self.year = 999
        self.References = []
        self.doi = ''


    def get_abbreviations_dict(self) -> dict:
        '''
        Get abbreviations and their meanings from the title and the abstract in a dictionary.
        Modified code from : https://gist.github.com/ijmarshall/b3d1de6ccf4fb8b5ee53
        :return:
        '''
        abstract_abbrevs = extract_abbreviation_definition_pairs(doc_text=self.Abstract)
        intro_abbrevs = extract_abbreviation_definition_pairs(doc_text=self.Introduction)
        abstract_abbrevs.update(intro_abbrevs)

        corrected_abbrevs = {}
        for k in abstract_abbrevs:
            corrected_abbrevs[' ' + k] = ' ' + abstract_abbrevs[k] + ' ' + '(' + k + ')'
        return corrected_abbrevs

    def replace_abbreviations(self):
        '''
        Replace each abbreviation (in title and abstract) by its meaning.
        :return:
        '''
        abbreviations_dict = self.get_abbreviations_dict()
        if abbreviations_dict:
            self.Abstract = multiple_replace(abbreviations_dict, self.Abstract)
            self.Title = multiple_replace(abbreviations_dict, self.Title)

    # def clean_text(self,text):
    #     '''
    #     clean the text based on TextCleaner object
    #     :param text:
    #     :return:
    #     '''
    #     cleaner = TextCleaner(text)
    #     cleaner.clean()
    #     return cleaner.cleaned_text

    def is_in_database(self,list_dois: list) -> bool:
        '''
        Check if the paper is already processed (its doi is in naimai database)
        :param list_dois: list of naimai dois
        :return:
        '''
        if self.doi in list_dois:
            return True
        return False

    def is_paper_english(self,nlp) -> bool:
        '''
        Detect language if paper language is english based on its title.
        :param nlp: spaCy nlp pipeline
        :return:
        '''
        if self.Title:
            title_nlp = nlp(self.Title)
            language_score=title_nlp._.language
            condition_english = (language_score['language']=='en') and (language_score['score']>0.7)
            if condition_english:
                return True
            else:
                return False
        return True

    def get_doi(self):
        '''
        Get doi of the paper
        :return:
        '''
        self.doi = self.paper_infos['doi']

    def get_fields(self) :
        '''
        Get list fields of the paper
        :return:
        '''
        self.fields = literal_eval(self.paper_infos['fields'])

    def get_Abstract(self):
        '''
        Get the abstract of the paper
        :return:
        '''
        abstract = self.paper_infos['abstract']
        if isinstance(abstract,str):
            self.Abstract = abstract.replace('-\n', '').replace('\n', ' ')
        else:
            self.Abstract = ''

    def get_Title(self):
        '''
        Get the title of the paper
        :return:
        '''
        self.Title = self.paper_infos['title'].replace('-\n', '').replace('\n', ' ')

    def get_Authors(self):
        '''
        Get the authors of the paper (in str format)
        :return:
        '''
        self.Authors = self.paper_infos['authors'].replace(';',',')

    
    def get_year(self):
        '''
        Get the year of publication of the paper
        :return:
        '''
        try:
            self.year = int(self.paper_infos['date'])
        except:
            self.year = ''
            print('Year to be corrected in ', self.doi)

    def save_dict(self) -> dict:
        '''
        Format the read data of the paper into a dictionary
        :return:
        '''
        attr_to_save = ['doi', 'Authors', 'year','database','fields','Abstract','Keywords', 'Title','numCitedBy','Journal']
        paper_to_save = {key: self.__dict__[key] for key in attr_to_save}
        return paper_to_save

    def get_journal(self):
        '''
        Get the journal of the paper
        :return:
        '''
        self.Journal = self.paper_infos['journals']

    def get_numCitedBy(self):
        '''
        Get the num of articles that cited this paper.
        :return:
        '''
        if 'numCitedBy' in self.paper_infos:
            self.numCitedBy = self.paper_infos['numCitedBy']
            if np.isnan(self.numCitedBy):
                self.numCitedBy = 0.5    
        else:
            path = path_open_citations + self.doi
            soup = get_soup(path)
            soup_list = literal_eval(soup.text)
            if isinstance(soup_list, list):
                self.numCitedBy = len(soup_list)

class papers:
    '''
    Class to process a csv file containing many papers data.
    '''
    def __init__(self, papers_path: str,database: str,nlp=None):
        '''
        :param papers_path: path of the csv file
        :param database: name of the database if all the papers in the csv file are coming from the same source.
        :param nlp:  spaCy nlp pipeline
        '''
        self.elements = {}
        self.database=database
        self.data = pd.read_csv(papers_path)
        print('Len data : ', len(self.data))

        # Getting nlp
        if nlp:
            self.nlp = nlp
        else:
            print('Loading nlp vocab..')
            self.nlp = spacy.load(nlp_vocab)
            Language.factory("language_detector", func=create_lang_detector)
            self.nlp.add_pipe('language_detector', last=True)

        # Getting naimai dois
        if os.path.exists(naimai_dois_path):
            self.naimai_dois = load_gzip(naimai_dois_path)
        else:
            # print('No naimai dois..')
            self.naimai_dois=[]

    def __len__(self):
        return len(self.elements.keys())

    def __setitem__(self, key, value):
        self.elements[key] = value

    def __getitem__(self, item):
        return self.elements[item]

    def random_papers(self,k=3, seed=None) -> list:
        '''
        Get random papers from the csv file.
        :param k: num of papers wanted
        :param seed: seed of random
        :return:
        '''
        elts = list(self.elements)
        random.seed(seed)
        rds = random.sample(elts, k)
        papers_list = [self.elements[el] for el in rds]
        return papers_list

    def add_paper(self,idx_in_data: int,check_database=True):
        '''
        Add a paper data as element
        :param idx_in_data: idx of the paper in the csv file
        :param check_database: if True, the paper is not added as element if already contained in the database.
        :return:
        '''
        new_paper = paper_base(df=self.data,
                                idx_in_df=idx_in_data)
        new_paper.get_doi()
        new_paper.get_Title()
        if check_database:
            is_in_database_condition = new_paper.is_in_database(self.naimai_dois)
        else:
            is_in_database_condition = False
        if not is_in_database_condition:
            if new_paper.is_paper_english(self.nlp):
                new_paper.get_Abstract()
                if len(new_paper.Abstract.split()) > 5:
                    new_paper.database = self.database
                    new_paper.get_fields()
                    new_paper.get_journal()
                    new_paper.get_Authors()
                    new_paper.get_year()
                    new_paper.replace_abbreviations()
                    new_paper.get_numCitedBy()
                    self.elements[new_paper.doi] = new_paper.save_dict()
                    self.naimai_dois.append(new_paper.doi)

    @update_naimai_dois
    def get_papers(self,update_dois=False,idx_start=0,idx_finish=-1,show_tqdm=False,check_database=True):
        '''
        Get the papers from the csv file and format them as a dictionary, stored as 'element' in the instance.
        :param update_dois: if True, it's going to update the list of naimai dois when new papers are added.
        :param idx_start: if >0, the processing starts from the idx_start^th row
        :param idx_finish: if != -1, the processing finishes at the idx_finish^th row
        :param show_tqdm: if True, a progress bar is showed to track the processing
        :param check_database: if True, the paper is not added as element if already contained in the database.
        :return:
        '''
        if show_tqdm:
            range_ = tqdm(self.data.iterrows(),total=len(self.data))
        else:
            range_= self.data.iterrows()
        for idx,_ in range_:
            self.add_paper(idx_in_data=idx,check_database=check_database)
            

    def save_elements(self, file_dir: str,update=False):
        '''
        Saves the dictionary of processed documents
        :param file_dir: path where the processed elements are stored.
        :param update: if True, update the file_dir in case it already exists.
        :return:
        '''
        papers_to_save = self.__dict__['elements']
        if update and os.path.exists(file_dir):
            loaded_papers = load_gzip(file_dir)
            loaded_papers.update(papers_to_save)
            save_gzip(file_dir,loaded_papers)
        else:
            save_gzip(file_dir,papers_to_save)


    def update_naimai_dois(self):
        '''
        Update the naimai dois if new dois are processed
        :return:
        '''
        if self.naimai_dois:
            save_gzip(naimai_dois_path,self.naimai_dois)

class paper_full_base(paper_base):
    '''
    Class to process the full article (instead of the abstract). [Not Finished].
    '''
    def __init__(self):
        super().__init__()
        self.Introduction = {}
        self.Methods = {}
        self.Results = {}
        self.unclassified_section = {}

    def get_abbreviations_dict(self):
        '''
        get all abbreviations of the papers in Introduction & Methods sections.
        :return:
        '''
        abstract_abbrevs={}
        if isinstance(self.Abstract,str):
            abstract_abbrevs = extract_abbreviation_definition_pairs(doc_text=self.Abstract)
        elif isinstance(self.Abstract,dict):
            for elt in self.Abstract:
                abstract_abbrevs = extract_abbreviation_definition_pairs(doc_text=self.Abstract[elt])
                abstract_abbrevs.update(abstract_abbrevs)

        for elt in self.Introduction:
            intro_abbrevs = extract_abbreviation_definition_pairs(doc_text=self.Introduction[elt])
            abstract_abbrevs.update(intro_abbrevs)
        for elt in self.Methods:
            methods_abbrevs = extract_abbreviation_definition_pairs(doc_text=self.Methods[elt])
            abstract_abbrevs.update(methods_abbrevs)

        corrected_abbrevs = {}
        for k in abstract_abbrevs:
            corrected_abbrevs[' ' + k] = ' ' + abstract_abbrevs[k] + ' ' + '(' + k + ')'
        return corrected_abbrevs

    def is_paper_english(self,nlp) -> bool:
        '''
        Detect language if paper language is english based on its title.
        :return:
        '''
        if self.Title:
            title_nlp = nlp(self.Title)
            language_score=title_nlp._.language
            condition_english = (language_score['language']=='en') and (language_score['score']>0.7)
            if condition_english:
                return True
        return False

    def save_dict(self):
        attr_to_save = ['doi', 'Authors', 'year','database','fields','Abstract','Keywords','Title','numCitedBy', 'Journal']
        paper_to_save = {key: self.__dict__[key] for key in attr_to_save}
        return paper_to_save