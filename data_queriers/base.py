from naimai.constants.paths import path_produced
from naimai.utils.general import clean_lst
from .sqlite_manager import SQLiteManager
import os
import re
import spacy
from naimai.constants.nlp import nlp_vocab
from naimai.constants.regex import regex_and_operators,regex_exact_match
from naimai.constants.models import threshold_tf_similarity
from naimai.models.papers_classification.tfidf import tfidf_model

class BaseQuerier:
  def __init__(self,field='', encoder=None, field_index=None,nlp=None,is_custom=True):
    self.encoder = encoder
    self.default_top_n = 200
    self.field = field
    self.field_index = field_index
    self.is_custom = is_custom

    if field:
      path_sqlite = os.path.join(path_produced, self.field, 'all_papers_sqlite')
      self.sql_manager = SQLiteManager(path_sqlite)
    self.search_operators = {'single': 0, "multiple": 1, "match":2}
    self.nlp = nlp
    self.load_nlp()

  def load_nlp(self):
      if not self.nlp:
          print('>> Loading nlp..')
          self.nlp = spacy.load(nlp_vocab)

  def remove_duplicated_fnames(self,list_fnames):
      '''
      remove duplicated fnames in list of results to keep only one paper per result
      :param list_fnames:
      :return:
      '''
      pattern = '_objectives|_methods|_results'
      only_fnames = [re.sub(pattern, '', elt) for elt in list_fnames]
      filtered_fnames = clean_lst(only_fnames)

      idxs_to_keep = []
      for fname in filtered_fnames:
        idxs_to_keep.append([idx for idx, elt in enumerate(list_fnames) if fname in elt][0])

      non_duplicated_fnames = [list_fnames[idx] for idx in idxs_to_keep]
      return non_duplicated_fnames


  # def get_corresponding_papers(self, wanted_papers_fnames: list, root_papers_fnames: list) -> list:
  #   '''
  #   XXX
  #   :param wanted_papers_fnames:
  #   :param root_papers_fnames:
  #   :return:
  #   '''
  #   root_fnames = [elt.replace('_objectives', '') for elt in root_papers_fnames]
  #
  #   results_papers_fnames = []
  #   for elt in root_fnames:
  #     for idx, pap in enumerate(wanted_papers_fnames):
  #       if elt in pap:
  #         results_papers_fnames.append(wanted_papers_fnames[idx])
  #
  #   return results_papers_fnames

  def sort_using_citations(self, papers: dict,top_n=5) -> list:
    '''
    Rank papers papers using numCitedBy parameter.
    :param papers:
    :return:
    '''
    nb_papers_ranked_CitedBy = len(papers)

    for fname in papers:
      if 'numCitedBy' not in papers[fname]:
        papers[fname]['numCitedBy'] = .5
    keys = list(papers.keys())
    papers_to_rank = [papers[fname] for fname in papers]
    papers_to_rank.sort(key=lambda x: float(x['numCitedBy']), reverse=True)
    fnames_ranked = [elt['fname'] for elt in papers_to_rank]
    rest_of_papers_fnames = [fname for fname in keys[nb_papers_ranked_CitedBy:]]
    papers_ranked = fnames_ranked + rest_of_papers_fnames
    return papers_ranked[:top_n]

  def sort_using_dates(self, papers, top_n) -> list:
    '''
    rank papers using their publications date
    :param papers:
    :param top_n:
    :return:
    '''

    nb_papers = len(papers)

    keys = list(papers.keys())
    papers_to_rank = [papers[fname] for fname in papers]
    papers_to_rank.sort(key=lambda x: float(x['year']), reverse=True)
    fnames_ranked = [elt['fname'] for elt in papers_to_rank]
    rest_of_papers_fnames = [fname for fname in keys[nb_papers:]]
    papers_ranked = fnames_ranked + rest_of_papers_fnames
    return papers_ranked[:top_n]

  def get_query_type(self, query: str) -> int:
    '''
    determine the query type : Simple operator (simple keywords), AND operator or exact match. OR operator is removed for the moment since it's rarely used.
    '''
    AND_operator = re.findall(regex_and_operators, query)
    exact_match = re.findall(regex_exact_match, query)

    if AND_operator:
      return self.search_operators['multiple']
    if exact_match:
      return self.search_operators['match']
    return self.search_operators['single']

  def get_papers_with_AND_operator(self,query,year_from=0,year_to=3000,top_n=200):
    '''
    overwrited method in custom_querier and with_keywords class
    '''
    return (None,None)

  def get_papers_for_tfidf_semantics(self,query,year_from=0,year_to=3000,top_n=200):
    '''
    overwrited method in custom_querier and with_keywords class
    '''
    return (None,None)

  def get_papers_with_exact_match(self,query,year_from=0,year_to=3000,top_n=200):
    '''
    overwrited method in custom_querier and with_keywords class
    '''
    return (None, None)

  def get_relevant_papers(self, query: str, query_type: int, year_from=0, year_to=3000, top_n=5) -> tuple:
    '''
    Get all similar papers & their fnames based on the query and query type. Here, we return tuple.
    Start with semantic search. If an operator is used, get the first 200 papers > apply operator
    :param query:
    :return:
    '''

    selected_papers, selected_papers_fnames= [],[]
    if query_type == self.search_operators['multiple']:  # AND operator
      selected_papers, selected_papers_fnames = self.get_papers_with_AND_operator(query,year_from=year_from,year_to=year_to,top_n=top_n)

    # elif query_type == 1:  # OR operator
    #   selected_papers, selected_papers_fnames = self.get_papers_with_OR_operator(query,year_from=year_from,year_to=year_to,top_n=top_n)

    elif query_type == self.search_operators['match']:  # exact match
      selected_papers, selected_papers_fnames = self.get_papers_with_exact_match(query,year_from=year_from,year_to=year_to,top_n=top_n)

    elif query_type == self.search_operators['single']:  # simple operator
      selected_papers, selected_papers_fnames = self.get_papers_for_tfidf_semantics(query,year_from=year_from,year_to=year_to,top_n=top_n)

    return selected_papers, selected_papers_fnames

  def sort_results(self,papers: dict,query: str,method='pertinence',top_n=5) -> list:
    '''
    Sort by 'pertinence', 'citations' or 'date'
    :param papers:
    :param query:
    :param method:
    :param top_n:
    :return:
    '''
    if self.is_custom:
      sorted_papers_fnames = [fname for fname in papers]
    else:
      sorted_papers_fnames = self.sort_using_tf_model(query, papers, top_n)

    if method == 'pertinence':
        return sorted_papers_fnames
    new_papers = {name: papers[name] for name in sorted_papers_fnames}

    if method =='citations':
        sorted_papers_fnames = self.sort_using_citations(new_papers,top_n)
        return sorted_papers_fnames
    elif method =='date':
        sorted_papers_fnames = self.sort_using_dates(new_papers, top_n)
        return sorted_papers_fnames
    return sorted_papers_fnames

  def sort_using_tf_model(self,query: str,papers: dict,top_n: int) -> list:
      tf = tfidf_model(query=query, papers=papers)
      tf.vectorizer.min_df = .05
      tf_ranked_papers_fnames, scores = tf.get_similar_fnames(top_n=top_n)

      if scores[0] < threshold_tf_similarity:
          print('>> WARNING : These results may not be relevant!')
      return tf_ranked_papers_fnames


  def find_papers(self, query: str, top_n=5, year_from=0, year_to=3000, verbose=False,sort_by='pertinence') -> list:
      '''
      Sort by 'pertinence', 'citations' or 'date'
      1. Get query type : simple operator, AND operator or exact match.
      2. Get 200 relevant papers and their fnames following the operator type
      3. Classify using a sorting method
      '''

      # 1. Get query type : simple operator, AND operator or exact match.
      query_type = self.get_query_type(query)
      if verbose:
          operator = [elt for elt in self.search_operators if self.search_operators[elt]==query_type][0]
          print('Operator: ', operator)

      # 2. Get all relevant papers and their fnames
      selected_papers, selected_papers_fnames = self.get_relevant_papers(query, query_type, year_from=year_from, year_to=year_to, top_n=self.default_top_n)
      if len(selected_papers)>self.default_top_n:
          print(f'More than {self.default_top_n} papers!')

      # 3. Classify using a sorting method
      if selected_papers:
          sorted_fnames = self.sort_results(selected_papers,query,sort_by,top_n)

          if verbose:
              print(' ')
          return sorted_fnames
      return []

  def review(self,query: str, top_n=100, sort_by='pertinence'):
    '''
    Generate a review
    :param query:
    :param top_n:
    :param sort_by:
    :return:
    '''

    papers = self.find_papers(query=query,top_n=top_n, sort_by=sort_by, verbose=False)
    reported_list = ['- ' + pap['reported'] for pap in papers if 'reported' in pap]
    review_text = '\n'.join(reported_list)
    return review_text

