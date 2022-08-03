from naimai.constants.paths import path_produced
from naimai.utils.general import get_root_fname
from naimai.constants.regex import regex_and_operators,regex_or_operators,regex_exact_match
from sentence_transformers import SentenceTransformer
from naimai.models.papers_classification.tfidf import tfidf_model
from naimai.data_sqlite import SQLiteManager
import faiss
import os
import re


class Querier:
  def __init__(self, field, encoder=None, field_index=None):
    self.encoder = encoder
    self.field = field
    self.field_index = field_index
    path_sqlite = os.path.join(path_produced, self.field, 'all_papers_sqlite')
    self.sql_manager = SQLiteManager(path_sqlite)

    if not encoder:
      print('>> Loading encoder..')
      self.load_encoder()

    if not field_index:
      print('>> Loading field index..')
      self.load_field_index()

  def keywords_in_paper(self,keywords: list,operator: int,paper: dict,papers:dict) -> bool:
    '''
    check if keywords are in papers following an operator
    '''
    fname = list(paper.keys())[0]

    if '_objectives' in fname:
      info = '. '.join(papers[fname]['messages']) + ' '+ papers[fname]['title']
    else:
      info = '. '.join(papers[fname]['messages'])

    if operator==0: #AND operator
      pattern = ''.join([f'(?:.*{kw})'for kw in keywords])
      if re.findall(pattern,info,flags=re.I):
        return True

    elif operator==1: #OR operator
      pattern = '|'.join(keywords)
      if re.findall(pattern,info,flags=re.I):
        return True

    elif operator==2: # exact match
      for query in keywords:
        if re.findall(query,info):
          return True

    return False

  def load_field_index(self):
    if not self.field_index:
      path = os.path.join(path_produced, self.field, 'encodings.index')
      self.field_index = faiss.read_index(path)

  def load_encoder(self):
    if not self.encoder:
      path = os.path.join(path_produced, self.field, 'search_model')
      self.encoder = SentenceTransformer(path)

  def get_corresponding_papers(self, wanted_papers_fnames: list, root_papers_fnames: list) -> list:
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

  def rank_papers_with_numCitedBy(self, papers: dict) -> list:
    '''
    Rank first papers papers using numCitedBy parameter
    :param papers:
    :return:
    '''
    nb_papers_ranked_CitedBy = 3
    for fname in papers:
      if 'numCitedBy' not in papers[fname]:
        papers[fname]['numCitedBy'] = .5
    keys = list(papers.keys())
    papers_to_rank = [papers[fname] for fname in keys[:nb_papers_ranked_CitedBy]]
    papers_to_rank.sort(key=lambda x: float(x['numCitedBy']), reverse=True)
    fnames_ranked = [elt['fname'] for elt in papers_to_rank]
    rest_of_papers_fnames = [fname for fname in keys[nb_papers_ranked_CitedBy:]]
    papers_ranked = fnames_ranked + rest_of_papers_fnames
    return papers_ranked

  def get_papers_with_exact_match(self,query: str, papers: dict) -> tuple:
    '''
    find papers for a query with exact match
    '''

    keywords = re.findall(regex_exact_match, query)
    selected_papers_fnames = []
    selected_papers = {}

    for fname in papers:
      paper = {fname : papers[fname]}
      if self.keywords_in_paper(keywords=keywords,operator=2,paper=paper, papers=papers):
        selected_papers_fnames.append(fname)
        selected_papers.update(paper)

    # selected_papers = self.sql_manager.search_with_exact_match(query)
    # selected_papers_fnames = list(selected_papers)
    return selected_papers, selected_papers_fnames


  def get_papers_with_OR_operator(self,query: str, papers: dict) -> tuple:
    '''
    find papers for a query with or operator
    '''

    keywords = [elt.strip() for elt in re.split(regex_or_operators,query)]
    selected_papers_fnames = []
    selected_papers = {}

    for fname in papers:
      paper = {fname : papers[fname]}
      if self.keywords_in_paper(keywords=keywords,operator=1,paper=paper):
        selected_papers_fnames.append(fname)
        selected_papers.update(paper)

    # selected_papers = self.sql_manager.search_with_OR_operator(query)
    # selected_papers_fnames = list(selected_papers)
    return selected_papers, selected_papers_fnames


  def get_papers_with_AND_operator(self,query: str, papers: dict) -> tuple:
    '''
    find papers for a query with and operator
    '''
    keywords = [elt.strip() for elt in re.split(regex_and_operators,query)]
    selected_papers_fnames = []
    selected_papers = {}

    for fname in papers:
      paper = {fname : papers[fname]}
      if self.keywords_in_paper(keywords=keywords,operator=0,paper=paper):
        selected_papers_fnames.append(fname)
        selected_papers.update(paper)

    return selected_papers, selected_papers_fnames

  def get_papers_with_semantics(self, query: str) -> tuple:
    '''
    find papers using encoder & field faiss index.
    '''
    default_top = 150
    encoded_query = self.encoder.encode([query])
    top_n_results = self.field_index.search(encoded_query, default_top)
    ids = top_n_results[1].tolist()[0]
    selected_papers = self.sql_manager.get_by_multiple_ids(ids)
    selected_papers_fnames = [selected_papers[elt]['fname'] for elt in selected_papers if
                              selected_papers[elt]['messages']]
    return selected_papers, selected_papers_fnames

  def get_all_similar_papers(self, query: str, query_type: int) -> tuple:
    '''
    Get all similar papers & their fnames based on the query and query type. Here, we return tuple instead of list of fnames
    as in custom querier to get return the papers too, instead of looking up for them each time.

    Start with semantic search. If an operator is used, get the first 200 papers > apply operator
    :param query:
    :return:
    '''

    selected_papers, selected_papers_fnames = self.get_papers_with_semantics(query)
    if query_type == 0:  # AND operator
      selected_papers, selected_papers_fnames = self.get_papers_with_AND_operator(query)

    elif query_type == 1:  # OR operator
      selected_papers, selected_papers_fnames = self.get_papers_with_OR_operator(query)

    elif query_type == 2:  # exact match
      selected_papers, selected_papers_fnames = self.get_papers_with_exact_match(query)

    return selected_papers, selected_papers_fnames

  def get_query_type(self, query):
    '''
    determine the query type : AND op (0), OR op (1), exact match (2),semantic (3)
    '''
    AND_operator = re.findall(regex_and_operators, query)
    OR_operator = re.findall(regex_or_operators, query)
    exact_match = re.findall(regex_exact_match, query)

    if AND_operator:
      return 0
    if OR_operator:
      return 1
    if exact_match:
      return 2
    return 3

  def get_similar_papers(self, query: str, top_n=5, year_from=0, year_to=3000, verbose=True) -> list:
    '''
    1. Get query type : AND op (0), OR op (1), exact match (2),semantic (3)
    2. Get all similar papers and their fnames
    3. Apply filter 1 : year range filter (need root fname)
    4. Reclassify using tf idf model (need corresponding fname)
    5. Rank first papers by numCitedBy using all_papers (need root fname)
    6. Get corresponding names
    '''

    # 1. Get query type : AND op (0), OR op (1), exact match (2),semantic (3)
    query_type = self.get_query_type(query)
    if verbose:
      print('Query type : ', query_type)

    # 2. Get all similar papers and their fnames using encoder & field faiss index
    if verbose:
      print('All similar papers selection..')
    selected_papers, selected_papers_fnames = self.get_all_similar_papers(query, query_type)

    if selected_papers:
      #  3. Apply year range filter :
      if verbose:
        print('Applying year range filter..')
      root_fnames = [get_root_fname(fname) for fname in selected_papers_fnames]
      root_papers_year_filtered = self.sql_manager.get_by_multiple_fnames(fnames=root_fnames,
                                                                          year_from=year_from,
                                                                          year_to=year_to)

      root_fnames_year_filtered = list(root_papers_year_filtered)
      # 4. Reclassify using tf idf model (need corresponding fname)
      corresponding_papers_fnames = self.get_corresponding_papers(selected_papers_fnames, root_fnames_year_filtered)
      corresponding_papers = {fname: selected_papers[fname] for fname in corresponding_papers_fnames}

      tf = tfidf_model(query=query, papers=corresponding_papers)
      tf_ranked_papers_fnames = tf.get_similar_fnames(top_n=top_n)

      # 5. Rank first papers by numCitedBy using all_papers (need root fname)
      ranked_root_fnames = [get_root_fname(fname) for fname in tf_ranked_papers_fnames]
      ranked_root_papers = {fname: root_papers_year_filtered[fname] for fname in ranked_root_fnames}
      ranked_root_fnames2 = self.rank_papers_with_numCitedBy(ranked_root_papers)

      # 6. Get corresponding names
      corresponding_papers_fnames2 = self.get_corresponding_papers(selected_papers_fnames, ranked_root_fnames2)
      return corresponding_papers_fnames2
    return []

