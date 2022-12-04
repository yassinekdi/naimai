import os
import numpy as np
import faiss
from tqdm.notebook import tqdm
from naimai.utils.general import load_gzip, save_gzip
from naimai.constants.fields import all_fields
from naimai.constants.paths import path_dispatched, path_similarity_model
from sentence_transformers import SentenceTransformer

class Dispatcher:
    '''
    Takes the formatted papers of a database and dispatches papers over the fields.
    Principle : Similarity between the papers data (fields or keywords) with the fields encoded & stored using faiss.
    '''
    def __init__(self, papers_dict, top_n=3, model=None, fields_index=None):
        self.papers = papers_dict
        self.top_n = top_n
        self.model = model
        self.fields_index = fields_index
        self.fields_elements = {k: {} for k in all_fields}

    def load_model(self, path=path_similarity_model):
        if not self.model:
            self.model = SentenceTransformer(path)

    def get_fields_index(self):
        encoded_fields = self.model.encode(all_fields)
        encoded_fields = np.asarray(encoded_fields.astype('float32'))
        self.fields_index = faiss.IndexIDMap(faiss.IndexFlatIP(768))
        self.fields_index.add_with_ids(encoded_fields, np.array(range(len(all_fields))))

    def query_from_fields(self, fields):
        return ', '.join(fields)

    def query_from_keywords(self, paper):
        return paper['Keywords']

    def query_from_title(self, paper):
        return paper['Title']

    def get_query(self, paper):
        fields = [elt for elt in paper['fields'] if isinstance(elt, str)]
        if len(fields) > 2:
            query = self.query_from_fields(fields)
        else:
            query = self.query_from_fields(fields) + ' ' + self.query_from_keywords(paper) + ' ' + self.query_from_title(
                paper)
        return query

    def paper2fields(self, paper):
        query = self.get_query(paper)
        query_vector = self.model.encode([query])
        ids = self.fields_index.search(query_vector, self.top_n)[1].tolist()[0]
        fields = list(np.array(all_fields)[ids])
        # paths = [os.path.join(path_dispatched,field) for field in fields]
        return fields

    def update_fields_elements(self, fname, paper, paper_fields):
        for field in paper_fields:
            self.fields_elements[field].update({fname: paper})

    def save_field_elements(self, field, file_name='all_papers', update=False):
        papers_field = self.fields_elements[field]
        path_field = os.path.join(path_dispatched, field, file_name)
        if update and os.path.exists(path_field):
            loaded_papers = load_gzip(path_field)
            loaded_papers.update(papers_field)
            save_gzip(path_field, loaded_papers)
        else:
            save_gzip(path_field, papers_field)

    def save_elements(self,file_name='all_papers', update=False):
        for field in tqdm(self.fields_elements):
            if self.fields_elements[field]:
                self.save_field_elements(field=field, file_name=file_name,update=update)

    def dispatch(self, save=False,file_name='all_papers', update=False):
        print('>> Initialization..')
        self.load_model()
        self.get_fields_index()
        print('>> Dispatching..')
        for fname in tqdm(self.papers):
            paper = self.papers[fname]
            paper_fields = self.paper2fields(paper)
            self.update_fields_elements(fname, paper, paper_fields)
        if save:
            print('>> Saving..')
            self.save_elements(update=update,file_name=file_name)
            print('>> Finished dispatching!')




