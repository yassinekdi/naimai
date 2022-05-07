import ast
import re
import pandas as pd
from tqdm.notebook import tqdm
from spacy_langdetect import LanguageDetector
from naimai.decorators import update_naimai_dois
import spacy

from naimai.papers.raw import papers, paper_base
from naimai.constants.paths import path_open_citations
from naimai.constants.regex import regex_spaced_chars,regex_keywords
from naimai.constants.nlp import nlp_vocab
from naimai.utils.regex import multiple_replace
from naimai.utils.general import get_soup


class paper_pmc(paper_base):
    def __init__(self ,df ,idx_in_df):
        super().__init__()
        self.database ="pmc"
        self.paper_infos = df.iloc[idx_in_df,:]

    def get_doi(self) -> str:
        self.doi = self.paper_infos['doi']

    def get_fields(self) -> list:
        '''
        get title + journal as fields. use it when you have title + journal
        :return:
        '''
        journal = re.sub('journal', '', self.Journal, flags=re.I)
        self.fields = [self.Title, journal]



    def get_Keywords_from_dict_abstract(self) -> str:
        '''
        get keywords from abstract when it's in a dict format & filter from abstract
        :return:
        '''
        for elt in self.Abstract:
            txt = self.Abstract[elt]
            keywords_in_txt = re.findall(regex_keywords, txt, re.I)
            if keywords_in_txt:
                self.Keywords = keywords_in_txt[0].strip()
                regex_filter = 'key\s?words:\s?' + self.Keywords
                self.Abstract[elt] = re.sub(regex_filter,'',txt,flags=re.I).strip()

    def get_Keywords_from_str_abstract(self)-> str:
        '''
        get keywords from abstract when it's in str format & filter from abstract
        :return:
        '''
        txt = self.Abstract
        keywords_in_txt = re.findall(regex_keywords, txt, re.I)
        if keywords_in_txt:
            self.Keywords = keywords_in_txt[0].strip()
            regex_filter = 'key\s?words:\s?' + self.Keywords
            self.Abstract = re.sub(regex_filter, '', txt, flags=re.I).strip()

    def get_Keywords(self) -> str:
        '''
        Get keywords from abstracts elements & remove them from abstract
        :return:
        '''
        if isinstance(self.Abstract,dict):
            self.get_Keywords_from_dict_abstract()
        elif isinstance(self.Abstract,str):
            self.get_Keywords_from_str_abstract()


    def get_Abstract(self) -> str:
        '''
        clean & stack (if stacked=True) abstract elements into one text & get Keywords from abstract.
        The spaced abstract case (a b s t r a c t..) is considered. if stacked = False, it puts the abstract elements in
        str format. It can returns in dict format if dict_format=True
        :return:
        '''
        abstract_dict_str = self.paper_infos['abstract']
        abstract_dict = ast.literal_eval(abstract_dict_str)
        if 'text' not in abstract_dict.keys():
            abstract_dict = {elt: ' '.join(abstract_dict[elt]) for elt in abstract_dict}

        for elt in abstract_dict:
            clean1=re.sub('abstract', '',abstract_dict[elt], flags=re.I).strip()
            clean2 = self.clean_text(clean1)
            abstract_dict[elt]=clean2

        abstract = ' '.join([elt for elt2 in list(abstract_dict.values()) for elt in elt2])
        no_space = re.findall('\w\w',abstract)
        if no_space: # normal case
            self.Abstract = abstract.replace('-\n', '').replace('\n', ' ')
        else: #spaced abstract, we "despace" 2 times
            despacing1 = re.sub(regex_spaced_chars, r'\1\2', abstract)
            self.Abstract = re.sub(regex_spaced_chars, r'\1\2', despacing1).replace('\n',' ')
        self.get_Keywords()

    def get_Title(self) -> str:
        self.Title = self.paper_infos['title'].replace('-\n', '').replace('\n', ' ')

    def get_Authors(self) -> str:
        authors_list_str = self.paper_infos['authors']
        authors_list = ast.literal_eval(authors_list_str)
        self.Authors = ', '.join(authors_list)

    def get_year(self) -> str:
        self.year = self.paper_infos['year']

    def get_journal(self) -> str:
        self.Journal =  self.paper_infos['journal']

    def get_numCitedBy(self) -> int:
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

# FIELDS AFTER TITLE JOURNAL
class papers_pmc(papers):
    def __init__(self, papers_path,nlp=None):
        super().__init__() # loading self.naimai_dois & other attributes
        self.data = pd.read_csv(papers_path)
        print('Len data : ', len(self.data))
        if nlp:
            self.nlp = nlp
        else:
            print('Loading nlp vocab..')
            self.nlp = spacy.load(nlp_vocab)
            self.nlp.add_pipe(LanguageDetector(), name='language_detector', last=True)

    def add_paper(self,idx_in_data):
            new_paper = paper_pmc(df=self.data,
                                    idx_in_df=idx_in_data)
            new_paper.get_doi()
            new_paper.get_Title()
            if new_paper.is_paper_english(self.nlp) and isinstance(new_paper.doi,str):
                if not new_paper.is_in_database(self.naimai_dois):
                    new_paper.get_Abstract()
                    new_paper.get_journal()
                    new_paper.get_fields()
                    new_paper.get_Authors()
                    new_paper.get_year()
                    new_paper.replace_abbreviations()
                    new_paper.get_numCitedBy()
                    self.elements[new_paper.doi] = new_paper.save_dict()
                    self.naimai_dois.append(new_paper.doi)


    @update_naimai_dois
    def get_papers(self,update_dois=False,idx_start=0,idx_finish=-1,show_tqdm=False):
        if show_tqdm:
            range_ = tqdm(self.data.iterrows(),total=len(self.data))
        else:
            range_= self.data.iterrows()
        for idx,_ in range_:
            self.add_paper(idx_in_data=idx)