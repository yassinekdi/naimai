from tqdm.notebook import tqdm
import pandas as pd
import numpy as np
from spacy_langdetect import LanguageDetector
import spacy
from naimai.constants.nlp import nlp_vocab

from naimai.utils.regex import multiple_replace
from naimai.papers.raw import papers, paper_base
from naimai.decorators import update_naimai_dois

class paper_egu(paper_base):
    def __init__(self,df,idx_in_df):
        super().__init__()
        self.database = 'egu'
        self.file_name = idx_in_df
        self.paper_infos = df.iloc[idx_in_df,:]

    def get_doi(self):
        self.doi = self.paper_infos['doi']

    def get_fields(self):
        self.fields = ['Environmental science',]

    def get_Abstract(self):
        self.Abstract = self.paper_infos['abstract'].replace('Abstract. ', '').replace('-\n', '').replace('\n', ' ')

    def get_Title(self):
        self.Title = self.paper_infos['title'].replace('-\n', '').replace('\n', ' ')

    def get_Authors(self):
        self.Authors = self.paper_infos['authors']

    def get_year(self):
        self.year = int(self.paper_infos['date'])

    def get_journal(self):
        self.Journal =  ''

    def replace_abbreviations(self):
        abbreviations_dict = self.get_abbreviations_dict()
        if abbreviations_dict:
            self.Abstract = multiple_replace(abbreviations_dict, self.Abstract)
            self.Title = multiple_replace(abbreviations_dict, self.Title)

    def get_numCitedBy(self):
        self.numCitedBy = self.paper_infos['numCitedBy']
        if np.isnan(self.numCitedBy):
            self.numCitedBy = 0.5


class papers_egu(papers):
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
            new_paper = paper_egu(df=self.data,
                                    idx_in_df=idx_in_data)
            new_paper.get_doi()
            new_paper.get_Title()
            if not new_paper.is_in_database(self.naimai_dois):
                if new_paper.is_paper_english(self.nlp):
                    new_paper.get_Abstract()
                    if len(new_paper.Abstract.split())>5:
                        new_paper.get_fields()
                        new_paper.get_journal()
                        new_paper.get_Authors()
                        new_paper.get_year()
                        new_paper.replace_abbreviations()
                        new_paper.get_numCitedBy()
                        self.elements[new_paper.doi] = new_paper.save_dict()
                        self.naimai_dois.append(new_paper.doi)


    @update_naimai_dois
    def get_papers(self,update_dois=False,idx_start=0,idx_finish=-1,show_tqdm=True):
        if show_tqdm:
            range_ = tqdm(self.data.iterrows(),total=len(self.data))
        else:
            range_= self.data.iterrows()
        for idx,_ in range_:
            self.add_paper(idx_in_data=idx)