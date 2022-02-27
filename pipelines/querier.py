from naimai.constants.paths import path_produced
from naimai.utils.general import load_gzip
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

  def load_field_index(self):
    if not self.field_index:
      path = os.path.join(path_produced,self.field,'encodings.index')
      self.field_index = faiss.read_index(path)

  def load_papers(self):
    if not self.papers:
      path = os.path.join(path_produced,self.field,'all_papers')
      self.papers = load_gzip(path)

  def load_encoder(self):
    if not self.encoder:
      path = os.path.join(path_produced, self.field, 'search_model')
      self.encoder = SentenceTransformer(path)

  def review(self,query, top_n=4,text=True):

    self.load_encoder()
    self.load_papers()
    self.load_field_index()

    encoded_query = self.encoder.encode([query])
    top_n = self.field_index.search(encoded_query,top_n)[1].tolist()
    ids = top_n[1].tolist()[0]
    distances = top_n[0].tolist()[0]
    fnames = list(self.papers.keys())
    similar_papers_fnames= list(np.unique(fnames)[ids])
    reported_texts = [self.papers[fn]['reported'] for fn in similar_papers_fnames]
    if text:
      return ' '.join(reported_texts)
    else:
      results = [(dist, report) for dist, report in zip(distances, reported_texts)]
      return results