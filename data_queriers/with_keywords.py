from .base import BaseQuerier
from naimai.utils.regex import lemmatize_query


class KeywordsQuerier(BaseQuerier):
    def __init__(self,field):
        super().__init__(field=field, is_custom=False)

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


