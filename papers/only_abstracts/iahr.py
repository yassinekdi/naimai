from tqdm.notebook import tqdm
import pandas as pd
from naimai.utils.regex import multiple_replace
from naimai.papers.raw import papers, paper_base
from naimai.decorators import update_naimai_dois

class paper_iahr(paper_base):
    def __init__(self,df,idx_in_df):
        super().__init__()
        self.database = 'iahr'
        self.file_name = idx_in_df
        self.paper_infos = df.iloc[idx_in_df,:]

    def get_doi(self):
        self.doi=self.paper_infos['webpage']

    def get_fields(self):
        self.fields = [self.paper_infos['field'],]

    def get_Abstract(self):
        self.Abstract = self.paper_infos['abstract']

    def get_Title(self):
        self.Title = self.paper_infos['title']

    def get_Authors(self):
        self.Authors = self.paper_infos['authors'].replace(';',',')

    def get_year(self):
        self.year = self.paper_infos['date']

    def get_journal(self):
        self.Journal =  'IAHR'

    def replace_abbreviations(self):
        abbreviations_dict = self.get_abbreviations_dict()
        if abbreviations_dict:
            self.Abstract = multiple_replace(abbreviations_dict, self.Abstract)
            self.Title = multiple_replace(abbreviations_dict, self.Title)

class papers_iahr(papers):
    def __init__(self, papers_path):
        super().__init__() # loading self.naimai_dois & other attributes
        self.data = pd.read_csv(papers_path)
        print('Len data : ', len(self.data))

    def add_paper(self,idx_in_data):
            new_paper = paper_iahr(df=self.data,
                                    idx_in_df=idx_in_data)
            new_paper.get_doi()
            if new_paper.doi:
                new_paper.get_Title()
                if not new_paper.is_in_database(self.naimai_dois):
                    new_paper.get_Abstract()
                    if len(new_paper.Abstract.split())>5:
                        new_paper.get_fields()
                        new_paper.get_journal()
                        new_paper.get_Authors()
                        new_paper.get_year()
                        new_paper.replace_abbreviations()
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