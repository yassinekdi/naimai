from naimai.constants.paths import path_produced
from naimai.utils.general import load_and_combine, get_root_fname
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
import os

class Querier:
  def __init__(self,field,encoder=None,field_index=None,papers={}):
    self.encoder=encoder
    self.field = field
    self.field_index=field_index
    self.papers= papers
    if not encoder:
      print('>> Loading encoder..')
      self.load_encoder()
    if not papers:
      print('>> Loading papers..')
      self.load_papers()
    if not field_index:
      print('>> Loading field index..')
      self.load_field_index()

  def load_field_index(self):
    if not self.field_index:
      path = os.path.join(path_produced,self.field,'encodings.index')
      self.field_index = faiss.read_index(path)

  def load_papers(self):
    if not self.papers:
      path = os.path.join(path_produced,self.field)
      self.papers = load_and_combine(path)

  def load_encoder(self):
    if not self.encoder:
      path = os.path.join(path_produced, self.field, 'search_model')
      self.encoder = SentenceTransformer(path)

  def idx_paper2numCitedBy(self,idx: int):
    '''
    find numCitedBy of an index of papers
    :param idx:
    :return:
    '''
    fnames = list(self.papers.keys())
    fname_idx = fnames[idx]
    root_fname = get_root_fname(fname_idx,fnames)
    numCitedBy = self.papers[root_fname]['numCitedBy']
    return numCitedBy

  def sort_idxs_bynumCitedBy(self,idxs: list):
    '''
    sort list of indices by numCitedBy
    :param idxs:
    :return:
    '''
    idxs_numCitedBy = [(idx, self.idx_paper2numCitedBy(idx)) for idx in idxs]
    idxs_numCitedBy.sort(key= lambda x: x[1])
    idxs_sorted = [elt[0] for elt in idxs_numCitedBy[::-1]]
    return idxs_sorted

  def get_similar_papers_fnames(self,query,top_n=5, year_from=0,year_to=3000):
    default_top=150
    encoded_query = self.encoder.encode([query])
    top_n_results = self.field_index.search(encoded_query, default_top)
    ids = top_n_results[1].tolist()[0]
    distances = top_n_results[0].tolist()[0]

    fnames = list(self.papers.keys())
    similar_papers_fnames = [fnames[elt] for elt in ids]

    # take years into account
    root_fnames = [get_root_fname(fname, fnames) for fname in similar_papers_fnames]
    root_fnames = [elt for elt in root_fnames if elt]
    years = [self.papers[elt]['year'] for elt in root_fnames]
    idxs_years_to_keep = [idx for idx, year in enumerate(years) if int(year) >= year_from and int(year) <= year_to]


    # take num of citations into account for the first 7 results
    idxs_to_rank = idxs_years_to_keep[:7]
    idxs_ranked = self.sort_idxs_bynumCitedBy(idxs_to_rank)
    idxs_results = idxs_ranked + idxs_years_to_keep[7:]

    # results
    results_papers = [self.papers[similar_papers_fnames[idx]] for idx in idxs_results][:top_n]
    results_distances = [distances[idx] for idx in idxs_results][:top_n]

    return (results_papers,results_distances)

  def review(self,query, top_n=4,text=True):
    pass

    # reported_texts = [self.papers[fn]['reported'] for fn in similar_papers_fnames]
    # if text:
    #   return ' '.join(reported_texts)
    # else:
    #   results = [(dist, report) for dist, report in zip(distances, reported_texts)]
    #   return results