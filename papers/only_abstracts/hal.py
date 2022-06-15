from tqdm.notebook import tqdm
import pandas as pd
from ast import literal_eval

from naimai.utils.regex import multiple_replace
from naimai.utils.general import get_soup
from naimai.papers.raw import papers, paper_base
from naimai.decorators import update_naimai_dois
from naimai.constants.paths import path_open_citations

class paper_hal(paper_base):
    def __init__(self,df,idx_in_df):
        super().__init__()
        self.database = 'hal'
        self.file_name = idx_in_df
        self.paper_infos = df.iloc[idx_in_df,:]

    def get_doi(self):
        self.doi = self.paper_infos['doi']

    def get_fields(self):
        self.fields = self.paper_infos['fields'].split(',')

    def get_Abstract(self):
        abstract = self.paper_infos['abstract']
        if isinstance(abstract,str):
            self.Abstract = abstract.replace('-\n', '').replace('\n', ' ')
        else:
            self.Abstract = ''

    def get_Title(self):
        self.Title = self.paper_infos['title'].replace('-\n', '').replace('\n', ' ')

    def get_Authors(self):
        self.Authors = self.paper_infos['authors']

    def get_year(self):
        try:
            self.year = int(self.paper_infos['date'])
        except:
            self.year = ''
            print('Year to be corrected in ', self.doi)

    def get_journal(self):
        self.Journal = self.paper_infos['journal']

    def replace_abbreviations(self):
        abbreviations_dict = self.get_abbreviations_dict()
        if abbreviations_dict:
            self.Abstract = multiple_replace(abbreviations_dict, self.Abstract)
            self.Title = multiple_replace(abbreviations_dict, self.Title)

    def get_numCitedBy(self):
        path = path_open_citations + self.doi
        soup = get_soup(path)
        soup_list = literal_eval(soup.text)
        if isinstance(soup_list, list):
            self.numCitedBy = len(soup_list)


class papers_hal(papers):
    def __init__(self, papers_path):
        super().__init__() # loading self.naimai_dois & other attributes
        self.data = pd.read_csv(papers_path)
        print('Len data : ', len(self.data))

    def add_paper(self,idx_in_data):
            new_paper = paper_hal(df=self.data,
                                    idx_in_df=idx_in_data)
            new_paper.get_doi()
            if not new_paper.is_in_database(self.naimai_dois):
                new_paper.get_Title()
                if new_paper.is_paper_english(self.nlp):
                    new_paper.get_Abstract()
                    if len(new_paper.Abstract.split()) > 5:
                        new_paper.get_fields()
                        new_paper.get_journal()
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