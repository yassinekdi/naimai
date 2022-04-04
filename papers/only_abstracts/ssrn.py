from tqdm.notebook import tqdm
import pandas as pd
import numpy as np
from habanero import Crossref
import re
import ast
from bs4 import BeautifulSoup

from naimai.utils.regex import multiple_replace
from naimai.constants.regex import regex_remove_from_ssrn_fields, regex_journal_names, regex_journal_names2
from naimai.constants.paths import path_open_citations
from naimai.papers.raw import papers, paper_base
from naimai.decorators import update_naimai_dois
from naimai.utils.general import get_doi_by_title, get_soup

tqdm.pandas()
class paper_ssrn(paper_base):
    def __init__(self,df,idx_in_df):
        super().__init__()
        self.database = 'ssrn'
        self.file_name = idx_in_df
        self.paper_infos = df.iloc[idx_in_df,:]


    def get_doi(self) -> str:
        doi = self.paper_infos['doi']
        if doi:
            self.doi = doi
        else:
            self.doi = 'https://papers.ssrn.com/sol3/papers.cfm?abstract_id='+ self.paper_infos['abstract_id']

    def get_fields(self) -> list:
        papers_field = self.paper_infos['papers_field']
        field = self.paper_infos['field']
        field_cleaned = re.sub(regex_remove_from_ssrn_fields,'',field).strip()
        self.fields = [field_cleaned,papers_field]

    def get_Abstract(self) -> str:
        self.Abstract = self.paper_infos['abstract_text'].replace('-\n', '').replace('\n', ' ').strip()

    def get_Title(self) -> str:
        self.Title = self.paper_infos['title'].replace('-\n', '').replace('\n', ' ').strip()

    def get_Authors(self) -> str:
        self.Authors = self.paper_infos['authors']

    def get_year(self) -> str:
        self.year = self.paper_infos['date']

    def get_journal(self) -> str:
        abstract_box = self.paper_infos['abstract_box']
        bs = BeautifulSoup(abstract_box, 'html.parser')
        journal = bs.find(name='div',attrs={'class': 'reference-info'})
        if journal:
            clean1 = re.sub(regex_journal_names,'',journal.text)
            self.Journal = re.sub(regex_journal_names2,'',clean1, flags=re.I).strip()
        else:
            self.Journal =  self.paper_infos['field']

    def replace_abbreviations(self):
        abbreviations_dict = self.get_abbreviations_dict()
        if abbreviations_dict:
            self.Abstract = multiple_replace(abbreviations_dict, self.Abstract)
            self.Title = multiple_replace(abbreviations_dict, self.Title)

    def get_numCitedBy(self) -> int:
        ssrn_page = 'https://papers.ssrn.com/sol3/papers.cfm?abstract_id'
        if ssrn_page not in self.doi:
            path = path_open_citations + self.doi
            soup = get_soup(path)
            soup_list = ast.literal_eval(soup.text)
            if isinstance(soup_list, list):
                self.numCitedBy = len(soup_list)

    def get_Keywords(self) -> str:
        keywords = self.paper_infos['keywords']
        if isinstance(keywords,str):
            self.Keywords = keywords.replace('Keywords: ', '')


class papers_ssrn(papers):
    def __init__(self, papers_path):
        super().__init__() # loading self.naimai_dois & other attributes
        self.data = pd.read_csv(papers_path)
        self.data['papers_field'] = papers_path.split('/')[-2]
        print('Len data : ', len(self.data))
        print('')
        print('Getting dois..')
        cr = Crossref()
        self.data['doi'] = self.data['title'].progress_apply(get_doi_by_title, args=(cr,))


    def add_paper(self,idx_in_data):
            new_paper = paper_ssrn(df=self.data,
                                    idx_in_df=idx_in_data)
            new_paper.get_doi()
            if not new_paper.is_in_database(self.naimai_dois):
                new_paper.get_Abstract()
                new_paper.get_fields()
                new_paper.get_Title()
                new_paper.get_journal()
                new_paper.get_Authors()
                new_paper.get_Keywords()
                new_paper.get_year()
                new_paper.replace_abbreviations()
                new_paper.get_numCitedBy()
                self.elements[new_paper.doi] = new_paper.save_dict()
                self.naimai_dois.append(new_paper.doi)


    @update_naimai_dois
    def get_papers(self,update_dois=False,idx_start=0,idx_finish=-1):
        for idx,_ in self.data.iterrows():
            self.add_paper(idx_in_data=idx)
