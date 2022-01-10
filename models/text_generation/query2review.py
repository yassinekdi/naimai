from paper2.models.papers_classification.semantic_search import Search_Model
from paper2.utils import transform_field_name
from paper2.constants.regex import regex_paper_year
from paper2.constants.paths import aws_root_pdfs, arxiv_pdfs_url, doi_url
import os
import re
import numpy as np

class Query_Reviewer:
    def __init__(self, field,encoder=None):
        self.field = field
        self.search_model = Search_Model(field=field, encoder=encoder)

        path_faiss = os.path.join('drive/MyDrive/MyProject/main_pipelines', field, 'encodings.index')
        path_papers = os.path.join('drive/MyDrive/MyProject/main_pipelines', field, 'df_naimai')
        self.search_model.load_naimai_data(path_papers)
        self.search_model.load_faiss_index(path_faiss)


    def choose_obj_in_mean_lengths_range(self,mean_objs):
        mean_lens = 22
        if len(mean_objs) == 1:
            print('21')
            return mean_objs[0]
        else:
            print('22')
            # take the closest len to the mean 22
            closest_to_mean = min(mean_objs, key=lambda x: abs(len(x.split()) - mean_lens))
            return closest_to_mean

    def choose_obj_beyond_mean_lengths_range(self, references):
        mean_lens_radius = np.arange(20, 26)
        closest_to_min_radius = min(references, key=lambda x: abs(len(x.split()) - mean_lens_radius[0]))
        return closest_to_min_radius

    def choose_objective(self, references):
        mean_lens_radius = np.arange(20, 26)
        if len(references) == 1:  # if only one ref, take it
            chosen = references[0]
            return chosen
        if len(references) > 1:  # keep lengths in mean lengths radius 20-25
            mean_objs = [elt for elt in references if len(elt.split()) in mean_lens_radius]
            if mean_objs:  # we have objs in the lengths radius:
                chosen = self.choose_obj_in_mean_lengths_range(mean_objs)
                return chosen
            else:  # so len(references)>1 and lengths of all refs are either < 20 (so we take the one with max length)
                # or > 26 (so we take the one with min length)
                chosen = self.choose_obj_beyond_mean_lengths_range(references)
                return chosen
        return

    def get_year(self,obj):
        year = re.findall(regex_paper_year, obj)
        if year:
            return int(year[0])
        return 0

    def get_ref_url(self,obj):
        database = obj['database']
        if database=="mine":
            url = os.path.join(aws_root_pdfs, 'Geophysics', transform_field_name(obj['filename']))
            return url
        if database=="arxiv":
            url = arxiv_pdfs_url + obj['filename']
            return url
        if database=="elsevier":
            url = doi_url + obj['filename']
            return url
        else:
            return '#'

    def obj_formulation(self,obj,prod=False):
        year = self.get_year(obj['objective'])

        if year:
            idx = obj['objective'].index(str(year))
            authors_part = obj['objective'][:idx + 5]
            objective_part = obj['objective'][idx + 5:]
            if prod:
                url = self.get_ref_url(obj)
                authors_part = "<b><a href={}>{}</a></b>".format(url, authors_part)

            return authors_part + objective_part
        return

    def write_by_relevance(self,list_objs):
        formulations = np.unique([self.obj_formulation(obj) for obj in list_objs])
        text = ' '.join(formulations)
        return text

    def write_by_time(self,list_objs):
        list_objs = sorted(list_objs, key=lambda x: self.get_year(x['objective']), reverse=True)
        text = self.write_by_relevance(list_objs)
        return text

    def review(self, query,top_n=7,order='Relevance'):
        objs_query = self.search_model.search(query=query,top_n=top_n)
        list_objs = [{'filename': elt[1]['filename'],
                        'objective': self.choose_objective(elt[1]['reported']),
                        'database': elt[1]['database']} for elt in objs_query]
        if order=='Relevance':
            return self.write_by_relevance(list_objs)
        else:
            return self.write_by_time(list_objs)

    test
