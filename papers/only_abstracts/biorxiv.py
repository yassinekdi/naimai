from tqdm.notebook import tqdm
import pandas as pd
from spacy_langdetect import LanguageDetector
import ast
import spacy

from naimai.utils.regex import multiple_replace
from naimai.constants.nlp import nlp_vocab
from naimai.constants.paths import path_open_citations
from naimai.papers.raw import papers, paper_base
from naimai.decorators import update_naimai_dois
from naimai.utils.general import get_soup

tqdm.pandas()

class paper_biorxiv(paper_base):
    def __init__(self,df,idx_in_df):
        super().__init__()
        self.database = 'biorxiv'
        self.file_name = idx_in_df
        self.paper_infos = df.iloc[idx_in_df,:]


    def get_doi(self) -> str:
        self.doi = self.paper_infos['doi']

    def get_fields(self) -> list:
        self.fields = [self.paper_infos['field_paper'],]

    def get_Abstract(self) -> str:
        self.Abstract = self.paper_infos['abstract'].replace('-\n', '').replace('\n', ' ').strip()

    def get_Title(self) -> str:
        self.Title = self.paper_infos['title'].replace('-\n', '').replace('\n', ' ').strip()

    def get_Authors(self) -> str:
        self.Authors = self.paper_infos['authors']

    def get_year(self) -> str:
        self.year = self.paper_infos['date']

    def get_journal(self) -> str:
        self.Journal =  'BioRxiv'

    def replace_abbreviations(self):
        abbreviations_dict = self.get_abbreviations_dict()
        if abbreviations_dict:
            self.Abstract = multiple_replace(abbreviations_dict, self.Abstract)
            self.Title = multiple_replace(abbreviations_dict, self.Title)

    def get_numCitedBy(self) -> int:
        path = path_open_citations + self.doi
        soup = get_soup(path)
        soup_list = ast.literal_eval(soup.text)
        if isinstance(soup_list,list):
            self.numCitedBy = len(soup_list)


class papers_biorxiv(papers):
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
            new_paper = paper_biorxiv(df=self.data,
                                    idx_in_df=idx_in_data)
            new_paper.get_doi()
            if new_paper.is_paper_english(self.nlp):
                if not new_paper.is_in_database(self.naimai_dois):
                    new_paper.get_Title()
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