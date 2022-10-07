from .base import BaseQuerier
from naimai.constants.paths import path_produced
from naimai.utils.general import get_root_fname
from sentence_transformers import SentenceTransformer
import faiss
import os


class SemanticsQuerier(BaseQuerier):
    def __init__(self, field,encoder=None, field_index=None):
        super().__init__(field=field)
        self.field = field
        self.encoder = encoder
        self.field_index = field_index

        self.load_encoder()
        self.load_field_index()


    def load_field_index(self):
        if not self.field_index:
            print('>> Loading field index..')
            path = os.path.join(path_produced, self.field, 'encodings.index')
            self.field_index = faiss.read_index(path)

    def load_encoder(self):
        if not self.encoder:
            print('>> Loading encoder..')
            path = os.path.join(path_produced, self.field, 'search_model')
            self.encoder = SentenceTransformer(path)


    def get_papers_with_bert_semantics(self, query: str, year_from=0, year_to=3000) -> tuple:
        '''
        find papers using encoder & field faiss index.
        '''
        default_top = 60
        encoded_query = self.encoder.encode([query])
        top_n_results = self.field_index.search(encoded_query, default_top)
        ids = top_n_results[1].tolist()[0]
        selected_papers = self.sql_manager.get_by_multiple_ids(ids,year_from=year_from,year_to=year_to)
        selected_papers_fnames = [selected_papers[elt]['fname'] for elt in selected_papers if
                                  selected_papers[elt]['messages']]

        selected_papers_fnames2 = self.remove_duplicated_fnames(selected_papers_fnames)
        selected_papers2 = {elt: selected_papers[elt] for elt in selected_papers_fnames2}
        return selected_papers2, selected_papers_fnames2

    # def find_papers(self, query: str, top_n=5, year_from=0, year_to=3000, verbose=True) -> list:
    #     '''
    #     1. Get query type : simple operator, AND operator or exact match.
    #     2. Get all relevant papers and their fnames
    #     4. Reclassify using tf idf model (need corresponding fname)
    #     5. Rank first papers by numCitedBy using all_papers (need root fname)
    #     6. Get corresponding names
    #     '''
    #
    #     # 1. Get query type : simple operator, AND operator or exact match.
    #     query_type = self.get_query_type(query)
    #     if verbose:
    #         operator = [elt for elt in self.search_operators if self.search_operators[elt]==query_type][0]
    #         print('Operator: ', operator)
    #
    #     # 2. Get all relevant papers and their fnames
    #     if verbose:
    #       print('>> All similar papers selection.. [base.py]')
    #     selected_papers, selected_papers_fnames = self.get_all_similar_papers(query, query_type,year_from=year_from,year_to=year_to,top_n=top_n)
    #
    #     if selected_papers:
    #       root_fnames = [get_root_fname(fname) for fname in selected_papers_fnames]
    #       # root_papers_year_filtered = self.sql_manager.get_by_multiple_fnames(fnames=root_fnames,
    #       #                                                                     year_from=year_from,
    #       #                                                                     year_to=year_to)
    #       # root_fnames_year_filtered = list(root_papers_year_filtered)
    #
    #       # 4. Reclassify using tf idf model (need corresponding fname)
    #       len_query = -1
    #       if query_type!=3:
    #         if verbose:
    #           print('>> Reclassify using tf idf.. [base.py]')
    #         corresponding_papers_fnames = self.get_corresponding_papers(selected_papers_fnames, root_fnames)
    #         corresponding_papers = {fname: selected_papers[fname] for fname in corresponding_papers_fnames}
    #
    #         tf = tfidf_model(query=query, papers=corresponding_papers)
    #         tf_ranked_papers_fnames, scores = tf.get_similar_fnames(top_n=top_n)
    #       else:
    #         # if more than 4 words in query, use tf idf
    #         lemmatized_query = lemmatize_query(self.nlp, query)
    #         len_query = len(lemmatized_query)
    #         if  len_query> 3:
    #           tf = tfidf_model(query=query, papers=selected_papers)
    #           tf.vectorizer.min_df = .05
    #           tf_ranked_papers_fnames, scores = tf.get_similar_fnames(top_n=top_n)
    #         else:
    #           tf_ranked_papers_fnames = selected_papers
    #           scores = [1]*len(tf_ranked_papers_fnames)
    #
    #       if scores[0] < threshold_tf_similarity:
    #         print('>> WARNING : These results may not be relevant!')
    #
    #       # 5. Rank first papers by numCitedBy using all_papers (need root fname)
    #       if verbose:
    #         print('>> numCitedBy Ranking.. [base.py]')
    #       tf_ranked_papers = {fname: selected_papers[fname] for fname in tf_ranked_papers_fnames}
    #       ranked_root_fnames2 = self.rank_papers_with_numCitedBy(tf_ranked_papers,len_query)
    #
    #       # 6. Get corresponding names
    #       corresponding_papers_fnames2 = self.get_corresponding_papers(selected_papers_fnames, ranked_root_fnames2)
    #       if verbose:
    #         print(' ')
    #       return corresponding_papers_fnames2
    #     return []
