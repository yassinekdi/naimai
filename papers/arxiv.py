from tqdm.notebook import tqdm
import dask.bag as db
import json
import re
import ast

from naimai.utils.regex import multiple_replace
from naimai.utils.general import get_soup
from naimai.papers.raw import papers, paper_base
from naimai.constants.fields import arxiv_fields_abbrevs, arxiv_fields_categories
from naimai.constants.regex import regex_year
from naimai.constants.paths import path_open_citations
from naimai.decorators import update_naimai_dois


class paper_arxiv(paper_base):
    def __init__(self,arxiv_id,metadata_df,idx_in_metadata_df,category):
        super().__init__()
        self.database = 'arxiv'
        self.file_name = arxiv_id
        self.metadata_df = metadata_df
        self.category = category
        self.idx = idx_in_metadata_df
        self.paper_infos = self.metadata_df.iloc[idx_in_metadata_df,:]

    def get_doi(self):
        self.doi = self.paper_infos['doi']

    def get_fields(self):
        field = self.category.split('.')[0]
        fields  = arxiv_fields_abbrevs[field] + ', ' + arxiv_fields_categories[field][self.category]
        self.fields = fields.replace('-', ',').split(',')

    def get_Abstract(self):
        self.Abstract = self.paper_infos['abstract'].replace('-\n', '').replace('\n', ' ')

    def get_Title(self):
        self.Title = self.paper_infos['title'].replace('-\n', '').replace('\n', ' ')

    def get_Authors(self):
        self.Authors = ', '.join([' '.join(at[::-1]) for at in self.paper_infos['authors_parsed']])

    def get_year(self):
        #self.year = year_from_arxiv_fname(self.file_name)
        self.year = self.paper_infos['year']

    def get_journal(self):
        self.journal =  self.paper_infos['journal-ref']

    def replace_abbreviations(self):
        abbreviations_dict = self.get_abbreviations_dict()
        if abbreviations_dict:
            self.Abstract = multiple_replace(abbreviations_dict, self.Abstract)
            self.Title = multiple_replace(abbreviations_dict, self.Title)

    def get_numCitedBy(self):
        if self.doi:
            path = path_open_citations + self.doi
            soup = get_soup(path)
            soup_list = ast.literal_eval(soup.text)
            if isinstance(soup_list,list):
                self.numCitedBy = len(soup_list)


class papers_arxiv(papers):
    def __init__(self, arxiv_metadata_dir,category):
        super().__init__() # loading self.naimai_dois & other attributes
        self.arxiv_metadata_dir = arxiv_metadata_dir
        self.category = category
        self.metadata_df = None
        self.abstracts = []
        self.titles = []
        self.authors = []
        self.files_ids = []
        # self.semantic_scholar = SemanticScholar(timeout=20)

    def get_infos(self):
        all_docs = db.read_text(self.arxiv_metadata_dir).map(json.loads)
        docs = all_docs.filter(lambda x: x['categories'] == self.category)
        filtered_docs = docs.filter(lambda x: x['comments'] != 'This paper has been withdrawn')
        print('>> Getting metadata_df..')
        self.metadata_df = filtered_docs.to_dataframe()[['id', 'authors_parsed', 'title', 'abstract', 'doi','journal-ref','versions']].compute()
        self.metadata_df['year'] = self.metadata_df['versions'].apply(lambda x: re.findall(regex_year, x[0]['created'])[0])
        self.files_ids = self.metadata_df['id']

    # @paper_reading_error_log_decorator
    def add_paper(self,arxiv_id,idx_in_metadata_df):
            new_paper = paper_arxiv(arxiv_id=arxiv_id,
                                    metadata_df=self.metadata_df,
                                    idx_in_metadata_df=idx_in_metadata_df,
                                    category=self.category)
            new_paper.get_doi()
            if not new_paper.is_in_database(self.naimai_dois):
                self.naimai_dois.append(new_paper.doi)
                new_paper.get_Abstract()
                new_paper.get_fields()
                new_paper.get_Title()
                new_paper.get_Authors()
                new_paper.get_year()
                new_paper.replace_abbreviations()
                new_paper.get_numCitedBy()
                self.elements[arxiv_id] = new_paper.save_dict()


    @update_naimai_dois
    def get_papers(self,update_dois=False,idx_start=0,idx_finish=-1):
        self.get_infos()
        files_ids=self.files_ids[idx_start,idx_finish]
        for idx_in_metadata_df,arxiv_id in tqdm(enumerate(files_ids), total=len(files_ids)):
            self.add_paper(arxiv_id=arxiv_id,idx_in_metadata_df=idx_in_metadata_df)

        print('Objs problem exported in objectives_pbs.txt')