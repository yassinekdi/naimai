from .base import BaseQuerier
from naimai.constants.paths import path_produced
from naimai.utils.general import get_root_fname
from naimai.utils.regex import lemmatize_query
from naimai.constants.regex import regex_and_operators,regex_exact_match
from naimai.constants.models import threshold_tf_similarity
from naimai.models.papers_classification.tfidf import tfidf_model
from .sqlite_manager import SQLiteManager
import os
import spacy
from naimai.constants.nlp import nlp_vocab
import re


class KeywordsQuerier(BaseQuerier):
    def __init__(self,field,nlp=None):
        super().__init__()
        self.field = field
        path_sqlite = os.path.join(path_produced, self.field, 'all_papers_sqlite')
        self.sql_manager = SQLiteManager(path_sqlite)
        self.nlp = nlp
        self.search_operators = {'simple_op': 0, "and_op": 1, "exact_match_op":2}
        self.load_nlp()

    def load_nlp(self):
        if not self.nlp:
            print('>> Loading nlp..')
            self.nlp = spacy.load(nlp_vocab)


    def get_papers_with_exact_match(self,query: str, year_from=0, year_to=3000,top_n=5) -> tuple:
        '''
        find papers for a query with exact match
        '''
        selected_papers = self.sql_manager.search_with_exact_match(query,year_from=year_from,year_to=year_to,top_n=top_n)
        selected_papers_fnames = list(selected_papers)
        return selected_papers, selected_papers_fnames


    def get_papers_with_OR_operator(self,query: str, year_from=0, year_to=3000,top_n=5) -> tuple:
        '''
        find papers for a query with or operator
        '''

        selected_papers = self.sql_manager.search_with_OR_operator(query,year_from=year_from,year_to=year_to,top_n=top_n)
        selected_papers_fnames = list(selected_papers)
        return selected_papers, selected_papers_fnames


    def get_papers_with_AND_operator(self,query: str, year_from=0, year_to=3000,top_n=5) -> tuple:
        '''
        find papers for a query with and operator
        '''

        selected_papers = self.sql_manager.search_with_AND_operator(query,year_from=year_from,year_to=year_to,top_n=top_n)
        selected_papers_fnames = list(selected_papers)
        return selected_papers, selected_papers_fnames

    def get_papers_for_tfidf_semantics(self,query: str, year_from=0, year_to=3000,top_n=5) -> tuple:
        '''
        find papers using tf idf
        :param query:
        :return:
        '''

        lemmatized_query = lemmatize_query(self.nlp,query)
        selected_papers = self.sql_manager.get_by_query_for_tf_model(lemmatized_query=lemmatized_query,year_from=year_from,year_to=year_to,top_n=top_n)
        selected_papers_fnames = list(selected_papers)
        return selected_papers, selected_papers_fnames


    def get_all_similar_papers(self, query: str, query_type: int, year_from=0, year_to=3000,top_n=5) -> tuple:
        '''
        Get all similar papers & their fnames based on the query and query type. Here, we return tuple instead of list of fnames
        as in custom querier to get return the papers too, instead of looking up for them each time.

        Start with semantic search. If an operator is used, get the first 200 papers > apply operator
        :param query:
        :return:
        '''

        selected_papers, selected_papers_fnames= [],[]
        if query_type == 0:  # AND operator
          selected_papers, selected_papers_fnames = self.get_papers_with_AND_operator(query,year_from=year_from,year_to=year_to,top_n=top_n)

        elif query_type == 1:  # OR operator
          selected_papers, selected_papers_fnames = self.get_papers_with_OR_operator(query,year_from=year_from,year_to=year_to,top_n=top_n)

        elif query_type == 2:  # exact match
          selected_papers, selected_papers_fnames = self.get_papers_with_exact_match(query,year_from=year_from,year_to=year_to,top_n=top_n)

        elif query_type == 3:  # semantics
          selected_papers, selected_papers_fnames = self.get_papers_for_tfidf_semantics(query,year_from=year_from,year_to=year_to,top_n=top_n)

        return selected_papers, selected_papers_fnames

    def get_query_type(self, query):
        '''
        determine the query type : Simple operator (simple keywords), AND operator or exact match. OR operator is removed for the moment since it's rarely used.
        '''
        AND_operator = re.findall(regex_and_operators, query)
        # OR_operator = re.findall(regex_or_operators, query)
        exact_match = re.findall(regex_exact_match, query)

        if AND_operator:
          return self.search_operators['and_op']
        if exact_match:
          return self.search_operators['exact_match_op']
        return self.search_operators['simple_op']


    def find_papers(self, query: str, top_n=5, year_from=0, year_to=3000, verbose=True) -> list:
        '''
        1. Get query type : simple operator, AND operator or exact match.
        2. Get all relevant papers and their fnames
        4. Reclassify using tf idf model (need corresponding fname)
        5. Rank first papers by numCitedBy using all_papers (need root fname)
        6. Get corresponding names
        '''

        # 1. Get query type : simple operator, AND operator or exact match.
        query_type = self.get_query_type(query)
        if verbose:
            operator = [elt for elt in self.search_operators if self.search_operators[elt]==query_type][0]
            print('Operator: ', operator)

        # 2. Get all relevant papers and their fnames
        if verbose:
          print('>> All similar papers selection.. [base.py]')
        selected_papers, selected_papers_fnames = self.get_all_similar_papers(query, query_type,year_from=year_from,year_to=year_to,top_n=top_n)

        if selected_papers:
          root_fnames = [get_root_fname(fname) for fname in selected_papers_fnames]

          len_query = -1
          if query_type!= self.search_operators['simple_op']:
            if verbose:
              print('>> Reclassify using tf idf.. [base.py]')
            corresponding_papers_fnames = self.get_corresponding_papers(selected_papers_fnames, root_fnames)
            corresponding_papers = {fname: selected_papers[fname] for fname in corresponding_papers_fnames}

            tf = tfidf_model(query=query, papers=corresponding_papers)
            tf_ranked_papers_fnames, scores = tf.get_similar_fnames(top_n=top_n)
          else:
            # if more than 4 words in query, use tf idf
            lemmatized_query = lemmatize_query(self.nlp, query)
            len_query = len(lemmatized_query)
            if  len_query> 3:
              tf = tfidf_model(query=query, papers=selected_papers)
              tf.vectorizer.min_df = .05
              tf_ranked_papers_fnames, scores = tf.get_similar_fnames(top_n=top_n)
            else:
              tf_ranked_papers_fnames = selected_papers
              scores = [1]*len(tf_ranked_papers_fnames)

          if scores[0] < threshold_tf_similarity:
            print('>> WARNING : These results may not be relevant!')

          # 5. Rank first papers by numCitedBy using all_papers (need root fname)
          if verbose:
            print('>> numCitedBy Ranking.. [base.py]')
          tf_ranked_papers = {fname: selected_papers[fname] for fname in tf_ranked_papers_fnames}
          ranked_root_fnames2 = self.rank_papers_with_numCitedBy(tf_ranked_papers,len_query)

          # 6. Get corresponding names
          corresponding_papers_fnames2 = self.get_corresponding_papers(selected_papers_fnames, ranked_root_fnames2)
          if verbose:
            print(' ')
          return corresponding_papers_fnames2
        return []