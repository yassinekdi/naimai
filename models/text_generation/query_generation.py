import random
from keybert import KeyBERT


class QueryGeneration:
    def __init__(self, nb_queries=2):
        self.nb_queries = nb_queries
        # self.queries = []
        self.keybert = KeyBERT()

    def from_message(self, message: str) -> list:
        '''
        get 2 keywords from message
        :param message:
        :return:
        '''
        keywords = self.keybert.extract_keywords(message, keyphrase_ngram_range=(2, 5), top_n=self.nb_queries)
        queries = [elt[0] for elt in keywords]
        return queries

    # def from_produced_paper(self,paper):
    #     if 'title' in paper.keys():
    #         title = paper['title']
    #         self.queries += self.from_message(title)

    #     messages = paper['messages']

    
    # def from_paragraphs(self, nb_queries_to_add):
    #     paragraph = self.paper['Abstract'].strip()+ ' ' + self.paper['Title'].strip()
    #     if paragraph:
    #         keywords = self.keybert.extract_keywords(paragraph, keyphrase_ngram_range=(1, 3),top_n=nb_queries_to_add)
    #         queries = [elt[0] for elt in keywords]
    #         try:
    #             three_random = random.sample(queries, k=nb_queries_to_add)
    #             self.queries += three_random
    #         except:
    #             pass
    #             # print('problem in paper {}, data base {}'.format(self.paper['file_name'],self.paper['database']))


    # def generate(self):
    #     self.queries = []
    #     self.from_keywords()
    #     self.from_title()
    #     self.queries = [elt for elt in self.queries if elt]
    #     len_queries = len(self.queries)
    #     nb_queries_to_add = self.nb_queries - len_queries
    #     self.from_paragraphs(nb_queries_to_add)
