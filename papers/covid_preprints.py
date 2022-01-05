import ast
from tqdm.notebook import tqdm
from paper2.papers.raw import papers, paper_base
import pandas as pd
from paper2.utils import replace_abbreviations

class paper_covid_preprint(paper_base):
    def __init__(self, data,obj_classifier_model=None):
        super().__init__(obj_classifier_model)
        self.database = 'covid preprint - '
        self.data = data

    def get_Abstract(self):
        self.Abstract = self.data['Abstract']

    def get_Title(self):
        self.Title = self.data['Title of preprint']

    def get_doi(self):
        self.doi = self.data['DOI']

    def get_Authors(self):
        self.Authors = ', '.join(ast.literal_eval(self.data['Authors']))

    def update_database(self):
        self.database = self.database + self.data['Uploaded Site']

    def get_Publication_year(self):
        self.Publication_year = self.data['Date of Upload'].split('-')[0]


class papers_covid_preprint(papers):

    def __init__(self, obj_classifier_model=None, author_classifier_model=None,
                 load_obj_classifier_model=True, load_author_classifier_model=False, load_nlp=True):
        super().__init__(obj_classifier_model=obj_classifier_model, author_classifier_model=author_classifier_model,
                         load_obj_classifier_model=load_obj_classifier_model,
                         load_author_classifier_model=load_author_classifier_model,
                         load_nlp=load_nlp)
        self.data = pd.read_csv('drive/MyDrive/MyProject/data/COVID-19-Preprint-Data_ver5.csv')

    def add_paper(self, idx, save_dict=True, report=True):
        data = self.data.iloc[idx, :]
        new_paper = paper_covid_preprint(data=data)
        new_paper.file_name = idx
        new_paper.get_Abstract()
        new_paper.get_Title()
        new_paper.get_doi()
        new_paper.get_Authors()
        new_paper.update_database()
        new_paper.get_Publication_year()
        new_paper = replace_abbreviations(new_paper)
        new_paper.get_objective_paper()
        if report:
          new_paper.report_objectives()
        if save_dict:
            self.elements[new_paper.file_name] = new_paper.save_paper_for_training()
            self.naimai_elements[new_paper.file_name] = new_paper.save_paper_for_naimai()
        else:
            self.elements[new_paper.file_name] = new_paper

    def get_papers(self, save_dict=True, report=True):
        for idx in tqdm(range(len(self.data))):
            self.add_paper(idx=idx, save_dict=save_dict, report=report)
