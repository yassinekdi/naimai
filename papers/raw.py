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


''' 
input papers in csv should have columns. Otherwise overwrite 
the method in paper & papers like in ISSN
'''
def create_lang_detector(nlp, name):
    return LanguageDetector()

class paper_base:
    def __init__(self,df,idx_in_df):
        self.pdf_path=''
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
        self.Emails = []
        self.doi = ''


    def get_abbreviations_dict(self):
        abstract_abbrevs = extract_abbreviation_definition_pairs(doc_text=self.Abstract)
        intro_abbrevs = extract_abbreviation_definition_pairs(doc_text=self.Introduction)
        conclusion_abbrevs = extract_abbreviation_definition_pairs(doc_text=self.Conclusion)
        abstract_abbrevs.update(intro_abbrevs)
        abstract_abbrevs.update(conclusion_abbrevs)

        corrected_abbrevs = {}
        for k in abstract_abbrevs:
            corrected_abbrevs[' ' + k] = ' ' + abstract_abbrevs[k] + ' ' + '(' + k + ')'
        return corrected_abbrevs

    # def clean_text(self,text):
    #     '''
    #     clean the text based on TextCleaner object
    #     :param text:
    #     :return:
    #     '''
    #     cleaner = TextCleaner(text)
    #     cleaner.clean()
    #     return cleaner.cleaned_text

    def is_in_database(self,list_dois):
        if self.doi in list_dois:
            return True
        return False

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
            else:
                return False
        return True

    def get_doi(self):
        self.doi = self.paper_infos['doi']

    def get_fields(self):
        # list
        self.fields = literal_eval(self.paper_infos['fields'])

    def get_Abstract(self):
        abstract = self.paper_infos['abstract']
        if isinstance(abstract,str):
            self.Abstract = abstract.replace('-\n', '').replace('\n', ' ')
        else:
            self.Abstract = ''

    def get_Title(self):
        self.Title = self.paper_infos['title'].replace('-\n', '').replace('\n', ' ')

    def get_Authors(self):
        self.Authors = self.paper_infos['authors'].replace(';',',')

    
    def get_year(self):
        try:
            self.year = int(self.paper_infos['date'])
        except:
            self.year = ''
            print('Year to be corrected in ', self.doi)

    def save_dict(self):
        attr_to_save = ['doi', 'Authors', 'year','database','fields','Abstract','Keywords', 'Title','numCitedBy','Journal']
        paper_to_save = {key: self.__dict__[key] for key in attr_to_save}
        return paper_to_save

    def get_journal(self):
        self.Journal = self.paper_infos['journals']

    def replace_abbreviations(self):
        abbreviations_dict = self.get_abbreviations_dict()
        if abbreviations_dict:
            self.Abstract = multiple_replace(abbreviations_dict, self.Abstract)
            self.Title = multiple_replace(abbreviations_dict, self.Title)

    def get_numCitedBy(self):
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
    def __init__(self, papers_path,database,nlp=None):
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
            print('No naimai dois..')
            self.naimai_dois=[]

    def __len__(self):
        return len(self.elements.keys())

    def __setitem__(self, key, value):
        self.elements[key] = value

    def __getitem__(self, item):
        return self.elements[item]

    def random_papers(self,k=3, seed=None):
        elts = list(self.elements)
        random.seed(seed)
        rds = random.sample(elts, k)
        papers_list = [self.elements[el] for el in rds]
        return papers_list

    def add_paper(self,idx_in_data,check_database=True):
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
        if show_tqdm:
            range_ = tqdm(self.data.iterrows(),total=len(self.data))
        else:
            range_= self.data.iterrows()
        for idx,_ in range_:
            self.add_paper(idx_in_data=idx,check_database=check_database)
            

    def save_elements(self, file_dir,update=False):
        papers_to_save = self.__dict__['elements']
        if update and os.path.exists(file_dir):
            loaded_papers = load_gzip(file_dir)
            loaded_papers.update(papers_to_save)
            save_gzip(file_dir,loaded_papers)
        else:
            save_gzip(file_dir,papers_to_save)


    def update_naimai_dois(self):
        if self.naimai_dois:
            save_gzip(naimai_dois_path,self.naimai_dois)

class paper_full_base(paper_base):
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