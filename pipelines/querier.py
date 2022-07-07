from naimai.constants.paths import path_produced
from naimai.utils.general import get_root_fname
from sentence_transformers import SentenceTransformer
from naimai.models.papers_classification.tfidf import tfidf_model
from naimai.data_sqlite import SQLiteManager
import faiss
import os
import re

class Querier:
  def __init__(self,field,encoder=None,field_index=None):
    self.encoder=encoder
    self.field = field
    self.field_index=field_index
    path_sqlite = os.path.join(path_produced, self.field, 'all_papers_sqlite')
    self.sql_manager = SQLiteManager(path_sqlite)

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

  def get_exact_match_papers(self, query: str) -> tuple:
    '''
    get only papers that has exact match of the query
    '''
    queries = re.findall('"(.*?)"', query)
    similar_papers = {}
    for one_query in queries:
      papers = self.sql_manager.get_by_query(one_query)
      similar_papers.update(papers)

    similar_papers_fnames = [similar_papers[elt]['fname'] for elt in similar_papers if similar_papers[elt]['messages']]
    return (similar_papers,similar_papers_fnames)

  def get_all_similar_papers(self, query: str) -> tuple:
    '''
    Get all similar papers & their fnames using a query
    :param query:
    :return:
    '''
    default_top = 50
    encoded_query = self.encoder.encode([query])
    top_n_results = self.field_index.search(encoded_query, default_top)
    ids = top_n_results[1].tolist()[0]
    similar_papers = self.sql_manager.get_by_multiple_ids(ids)
    similar_papers_fnames = [similar_papers[elt]['fname'] for elt in similar_papers if similar_papers[elt]['messages']]
    return (similar_papers, similar_papers_fnames)

  def get_corresponding_papers(self, wanted_papers_fnames, root_papers_fnames) -> list:
    root_fnames = [elt.replace('_objectives', '') for elt in root_papers_fnames]

    results_papers_fnames = []
    for elt in root_fnames:
      for idx, pap in enumerate(wanted_papers_fnames):
        if elt in pap:
          results_papers_fnames.append(wanted_papers_fnames[idx])

    return results_papers_fnames

  def get_nb_words_in_messages(self, query: str, messages: list) -> int:
    '''
    find total nb of query words in list of messages
    '''

    pattern = re.compile('|'.join(query.split()))
    len_words = 0
    for message in messages:
      len_words += len(re.findall(pattern, message))

    return len_words

  # def rank_by_query_words(self, query: str, papers: dict, top_n) -> dict:
  #   track_list = []
  #   for fname in papers:
  #     messages = papers[fname]['messages']
  #     nb_words_in_query = self.get_nb_words_in_messages(query, messages)
  #     track_list.append((fname, nb_words_in_query))
  #
  #   track_list.sort(key=lambda x: x[1], reverse=True)
  #   sorted_papers = {elt[0]: papers[elt[0]] for elt in track_list[:top_n]}
  #   return sorted_papers

  def rank_papers_with_numCitedBy(self, papers: dict) -> list:
    '''
    Rank first papers papers using numCitedBy parameter
    :param papers:
    :return:
    '''
    nb_papers_ranked_CitedBy = 3
    for fname in papers:
      if 'numCitedBy' not in papers[fname]:
        papers[fname]['numCitedBy']=.5
    keys = list(papers.keys())
    papers_to_rank = [papers[fname] for fname in keys[:nb_papers_ranked_CitedBy]]
    papers_to_rank.sort(key=lambda x: float(x['numCitedBy']), reverse=True)
    fnames_ranked = [elt['fname'] for elt in papers_to_rank]
    rest_of_papers_fnames = [fname for fname in keys[nb_papers_ranked_CitedBy:]]
    papers_ranked = fnames_ranked + rest_of_papers_fnames
    return papers_ranked

  def get_similar_papers(self, query: str, top_n=5, year_from=0, year_to=3000) -> list:
    '''
    1. Get all similar papers and their fnames
    2. Get all_papers, papers in range of selected years with root fnames
    3. Find corresponding papers to root fnames ranked
    4. Reclassify using tf idf model
    5. Rank first papers by numCitedBy using all_papers
    :param query:
    :param top_n:
    :param year_from:
    :param year_to:
    :return:
    '''

    # 1. Get all similar papers and their fnames
    exact_match=re.findall('"(.*?)"', query)
    if exact_match:
      similar_papers, similar_papers_fnames = self.get_exact_match_papers(query)
    else:
      similar_papers, similar_papers_fnames = self.get_all_similar_papers(query)

    # 2.Get papers in range of selected years using their root fnames
    root_fnames = [get_root_fname(fname) for fname in similar_papers_fnames]

    papers_in_year_range = self.sql_manager.get_by_multiple_fnames(fnames=root_fnames,
                                                                   year_from=year_from,
                                                                   year_to=year_to)
    papers_in_year_range_fnames = list(papers_in_year_range.keys())

    # 3. Find corresponding papers using papers in year range
    corresponding_papers_fnames = self.get_corresponding_papers(similar_papers_fnames, papers_in_year_range_fnames)
    corresponding_papers = {fname: similar_papers[fname] for fname in corresponding_papers_fnames}

    # 4. Reclassify using tf idf model
    tf = tfidf_model(query=query, papers=corresponding_papers)
    ranked_papers_fnames = tf.get_similar_fnames(top_n=top_n)
    # ranked_papers = self.rank_by_query_words(query,corresponding_papers,top_n)
    # ranked_papers_fnames = list(ranked_papers.keys())

    # 5. Rerank root papers by numCited By
    ranked_root_fnames = [get_root_fname(fname) for fname in ranked_papers_fnames]
    ranked_root_papers = {fname: papers_in_year_range[fname] for fname in ranked_root_fnames}
    ranked_root_fnames2 = self.rank_papers_with_numCitedBy(ranked_root_papers)

    # 6. Get corresponding papers
    corresponding_papers_fnames2 = self.get_corresponding_papers(similar_papers_fnames, ranked_root_fnames2)

    return corresponding_papers_fnames2

