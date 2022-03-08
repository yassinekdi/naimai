from tqdm.notebook import tqdm
import pandas as pd
import numpy as np

from naimai.utils.regex import multiple_replace
from naimai.papers.raw import papers, paper_base
from naimai.decorators import update_naimai_dois

class paper_issn(paper_base):
    def __init__(self,df,idx_in_df):
        super().__init__()
        self.database = 'issn'
        self.file_name = idx_in_df
        self.paper_infos = df.iloc[idx_in_df,:]

    def get_doi(self):
        self.doi = self.paper_infos['doi']

    def get_fields(self):
        self.fields = [self.paper_infos['field_paper'], self.paper_infos['field_issn']]

    def get_Abstract(self):
        self.Abstract = self.paper_infos['abstract'].replace('-\n', '').replace('\n', ' ')

    def get_Title(self):
        self.Title = self.paper_infos['title'].replace('-\n', '').replace('\n', ' ')

    def get_Authors(self):
        self.Authors = self.paper_infos['authors']

    def get_year(self):
        self.year = self.paper_infos['date']

    def get_journal(self):
        self.Journal =  self.paper_infos['field_issn']

    def replace_abbreviations(self):
        abbreviations_dict = self.get_abbreviations_dict()
        if abbreviations_dict:
            self.Abstract = multiple_replace(abbreviations_dict, self.Abstract)
            self.Title = multiple_replace(abbreviations_dict, self.Title)

    def get_numCitedBy(self):
        self.numCitedBy = self.paper_infos['numCitedBy']
        if np.isnan(self.numCitedBy):
            self.numCitedBy = 0.5


class papers_issn(papers):
    def __init__(self, papers_path):
        super().__init__() # loading self.naimai_dois & other attributes
        self.data = pd.read_csv(papers_path)
        print('Len data : ', len(self.data))

    def add_paper(self,idx_in_data):
            new_paper = paper_issn(df=self.data,
                                    idx_in_df=idx_in_data)
            new_paper.get_doi()
            if not new_paper.is_in_database(self.naimai_dois):
                self.naimai_dois.append(new_paper.doi)
                new_paper.get_Abstract()
                new_paper.get_fields()
                new_paper.get_Title()
                new_paper.get_journal()
                new_paper.get_Authors()
                new_paper.get_year()
                new_paper.replace_abbreviations()
                new_paper.get_numCitedBy()
                self.elements[str(idx_in_data)] = new_paper.save_dict()


    @update_naimai_dois
    def get_papers(self,update_dois=False,idx_start=0,idx_finish=-1):
        for idx,_ in tqdm(self.data.iterrows(),total=len(self.data)):
            self.add_paper(idx_in_data=idx)
        print('Objs problem exported in objectives_pbs.txt')