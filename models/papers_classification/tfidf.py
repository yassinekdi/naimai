import numpy as np
import pandas as  pd
from sklearn.metrics.pairwise import linear_kernel
from sklearn.feature_extraction.text import TfidfVectorizer

class tfidf_model:
    def __init__(self, query: str, papers: dict, vectorizer=None):
        self.papers = papers
        self.papers_fnames = ['query'] + [fname for fname in papers]
        self.query = query
        self.corpus = []
        self.encodings = None
        if vectorizer:
            self.vectorizer = vectorizer
        else:
            self.vectorizer = TfidfVectorizer(use_idf=True, stop_words="english")

    def paper2doc(self, paper: dict) -> str:
        '''
        transform paper dict to a document : text from its messages
        '''
        messages = ' '.join(paper['messages'])
        return messages

    def build_corpus(self) -> list:
        '''
        build corpus based on the messages of papers : list of texts from messages of papers
        '''
        corpus = [self.query, ]
        for fname in self.papers:
            paper = self.papers[fname]
            doc = self.paper2doc(paper)
            corpus.append(doc)
        self.corpus = corpus

    def get_tf_encodings(self):
        '''
        get tf encodings by computing tfidf scores
        '''
        encodings = self.vectorizer.fit_transform(self.corpus).toarray()
        encodings_df = pd.DataFrame(encodings, columns=self.vectorizer.get_feature_names(), index=self.papers_fnames)
        df = encodings_df.T[(encodings_df.T > 0).any(1)]
        self.encodings = df.T

    def most_similar(self, top_n=5) -> list:
        '''
        get fnames of similar papers using encodings
        '''
        cosine_scores = linear_kernel(self.encodings, self.encodings)
        cos_score = np.array(cosine_scores[0])
        most_sims = np.argsort(cos_score)[::-1][1:(top_n + 1)]
        similar_fnames = [self.papers_fnames[idx] for idx in most_sims]
        # result = [(message, cos_score[i]) for message, i in zip(similar_messages, most_sims) if cos_score[i]>0]
        return similar_fnames

    def get_similar_fnames(self, top_n=20) -> list:
        ''' get similar fnames '''
        self.build_corpus()
        self.get_tf_encodings()
        fnames = self.most_similar(top_n=top_n)
        return fnames