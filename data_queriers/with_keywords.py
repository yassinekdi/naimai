from .base import BaseQuerier
from naimai.constants.paths import path_produced
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
        super().__init__(field=field)
        self.field = field
        path_sqlite = os.path.join(path_produced, self.field, 'all_papers_sqlite')
        self.sql_manager = SQLiteManager(path_sqlite)
        self.nlp = nlp
        self.search_operators = {'single': 0, "multiple": 1, "match":2}
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
        selected_papers = self.sql_manager.get_by_lemmatized_query(lemmatized_query=lemmatized_query, year_from=year_from, year_to=year_to, top_n=top_n)
        selected_papers_fnames = list(selected_papers)
        return selected_papers, selected_papers_fnames


    def get_relevant_papers(self, query: str, query_type: int, year_from=0, year_to=3000, top_n=5) -> tuple:
        '''
        Get all similar papers & their fnames based on the query and query type. Here, we return tuple instead of list of fnames
        as in custom querier to get return the papers too, instead of looking up for them each time.

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

    def sort_results(self,papers: dict,query: str,method='pertinence',top_n=5) -> list:
        '''
        Sort by 'pertinence', 'citations' or 'date'
        :param papers:
        :param query:
        :param method:
        :param top_n:
        :return:
        '''
        sorted_papers_fnames=[]
        if method == 'pertinence':
            sorted_papers_fnames = self.sort_using_tf_model(query, papers, top_n)
        elif method =='citations':
            sorted_papers_fnames = self.sort_using_citations(papers,top_n)
        elif method =='date':
            sorted_papers_fnames = self.sort_using_dates(papers, top_n)
        return sorted_papers_fnames

    def sort_using_tf_model(self,query: str,papers: dict,top_n: int) -> list:
        tf = tfidf_model(query=query, papers=papers)
        tf.vectorizer.min_df = .05
        tf_ranked_papers_fnames, scores = tf.get_similar_fnames(top_n=top_n)

        if scores[0] < threshold_tf_similarity:
            print('>> WARNING : These results may not be relevant!')
        return tf_ranked_papers_fnames




    def find_papers(self, query: str, top_n=5, year_from=0, year_to=3000, verbose=True,sort_by='pertinence') -> list:
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
        if verbose:
          print('>> All similar papers selection.. [base.py]')
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