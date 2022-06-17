from naimai.constants.paths import path_produced
from naimai.utils.general import get_root_fname
from sentence_transformers import SentenceTransformer
from data_sqlite import SQLiteManager
import faiss
import os

class Querier:
  def __init__(self,field,encoder=None,field_index=None,path_sqlite=''):
    self.encoder=encoder
    self.field = field
    self.field_index=field_index
    self.path_sqlite = path_sqlite
    if not encoder:
      print('>> Loading encoder..')
      self.load_encoder()

    if not field_index:
      print('>> Loading field index..')
      self.load_field_index()

  def load_field_index(self):
    if not self.field_index:
      path = os.path.join(path_produced,self.field,'encodings.index')
      self.field_index = faiss.read_index(path)

  def load_encoder(self):
    if not self.encoder:
      path = os.path.join(path_produced, self.field, 'search_model')
      self.encoder = SentenceTransformer(path)

  def get_similar_papers(self,query,top_n=5, year_from=0,year_to=3000):
    '''
    Get similar papers > get their fnames > their root fnames > find papers in range of years > rank by numCitedBy
    > find corresponding papers
    :param query:
    :param top_n:
    :param year_from:
    :param year_to:
    :return:
    '''
    default_top=150
    encoded_query = self.encoder.encode([query])
    top_n_results = self.field_index.search(encoded_query, default_top)
    ids = top_n_results[1].tolist()[0]

    sql = SQLiteManager(self.path_sqlite)
    similar_papers = sql.get_by_multiple_ids(ids)

    # get fnames
    similar_papers_fnames = [elt[10] for elt in similar_papers]

    # get root fnames
    root_fnames = [get_root_fname(fname) for fname in similar_papers_fnames]

    # papers_in_year_range
    papers_in_year_range = sql.get_by_multiple_fnames(fnames=root_fnames,
                                                      year_from=year_from,
                                                      year_to=year_to)

    # rank first 7 by numCited By
    papers_to_rank = papers_in_year_range[:7]
    papers_to_rank.sort(key=lambda x: float(x[9]))
    papers_in_year_range_ranked = papers_to_rank[::-1] + papers_in_year_range[7:]

    # get corresponding papers
    root_fnames_in_year_range = [elt[10].replace('_objectives', '') for elt in papers_in_year_range_ranked]

    similar_fnames_papers_in_year_range = []
    for elt in root_fnames_in_year_range:
      for idx, pap in enumerate(similar_papers_fnames):
        if elt in pap:
          similar_fnames_papers_in_year_range.append(similar_papers_fnames[idx])

    similar_papers.sort(key=lambda x: similar_fnames_papers_in_year_range.index(x[10]))

    # results
    results_papers = similar_papers[:top_n]
    return results_papers

