import random
from keybert import KeyBERT


class QueryGeneration:
    def __init__(self, training_paper_dict, nlp, nb_queries=6):
        self.nb_queries = nb_queries
        self.paper = training_paper_dict
        self.queries = []
        self.nlp = nlp
        self.keybert = KeyBERT()

    def from_keywords(self):
        # 3 queries from keywords
        if self.paper['Keywords']:
            kwords = self.paper['Keywords'].split(',')
            kwords = [elt.strip() for elt in kwords if elt]
            if len(kwords)>2:
                result = random.sample(kwords, k=2)
            elif len(kwords)==1:
                result = kwords
            else:
                result = []
            self.queries += result

    def from_title(self):
        #  remove .replace('-\n', '').replace('\n', ' ') after
        if self.paper['Title']:
            title = self.paper['Title'].replace('-\n', '').replace('\n', ' ')
            stc_nlp = self.nlp(title)
            # extract noun& propn & adj
            pos_list = ['NOUN', 'ADJ', 'PROPN']
            kwords = [word.text.strip() for word in stc_nlp if word.pos_ in pos_list]
            self.queries += [' '.join(kwords)]

    def from_paragraphs(self, nb_queries_to_add):

        paragraph = self.paper['Abstract'].strip() + ' ' + self.paper['Conclusion'].strip()
        if paragraph:
            keywords = self.keybert.extract_keywords(paragraph, keyphrase_ngram_range=(1, 3),top_n=nb_queries_to_add)
            queries = [elt[0] for elt in keywords]
            try:
                three_random = random.sample(queries, k=nb_queries_to_add)
                self.queries += three_random
            except:
                print('problem in paper {}, data base {}'.format(self.paper['file_name'],self.paper['database']))


    def generate(self):
        self.queries = []
        self.from_keywords()
        self.from_title()
        self.queries = [elt for elt in self.queries if elt]
        len_queries = len(self.queries)
        nb_queries_to_add = self.nb_queries - len_queries
        self.from_paragraphs(nb_queries_to_add)
