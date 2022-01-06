import random
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import pickle, gzip, pickletools
import spacy
from pathlib import Path
from tqdm.notebook import tqdm

from paper2.processing import ArticleToProcess
from paper2.constants.paths import path_nlp

class tfIdf_model:

    def __init__(self, all_papers, nlp=None, shuffle=True):
        self.nlp = nlp
        if not nlp:
            self.nlp = spacy.load(Path(path_nlp))
            self.nlp.max_length = 20000000

        self.vectorizer = TfidfVectorizer(use_idf=True)  # TfidfVectorizer(ngram_range = (2, 2))
        if shuffle:
            self.papers = random.sample(all_papers, len(all_papers))
        else:
            self.papers = all_papers

        self.encodings = np.ones(2)
        self.cosine_scores = np.ones(2)
        self.documents = []
        self.corpus = []

    def set_threshold(self, list_paragraphs,threshold):
        new_list_paragraphs=[]
        for paragraph in list_paragraphs:
            split = paragraph.split()[:threshold]
            join = ' '.join(split)
            new_list_paragraphs.append(join)
        return new_list_paragraphs

    def update_documents(self,papers):
        introductions = self.get_Introductions(papers)
        abstracts = self.get_Abstracts(papers)
        conclusions = self.get_Conclusions(papers)
        keywords = self.get_keywords(papers)

        introductions_filtered = self.set_threshold(introductions,20000)
        abstracts_filtered  = self.set_threshold(abstracts,1500)
        conclusions_filtered  = self.set_threshold(conclusions,10000)
        keywords_filtered = self.set_threshold(keywords,15000)

        return [intro + '. ' + abst +'. '+ conclu+ '. ' + kwords for intro, abst, conclu, kwords in zip(introductions_filtered, abstracts_filtered,conclusions_filtered, keywords_filtered)]

    def get_documents(self):
        introductions = self.get_Introductions()
        abstracts = self.get_Abstracts()
        conclusions = self.get_Conclusions()
        keywords = self.get_keywords()

        introductions_filtered = self.set_threshold(introductions, 20000)
        abstracts_filtered = self.set_threshold(abstracts, 1500)
        conclusions_filtered = self.set_threshold(conclusions, 10000)
        keywords_filtered = self.set_threshold(keywords, 15000)

        self.documents = [intro + '. ' + abst +'. '+ conclu+ '. ' + kwords for intro, abst, conclu, kwords in zip(introductions_filtered, abstracts_filtered,conclusions_filtered, keywords_filtered)]

    def get_Introductions(self,papers_list=[]):
        if papers_list:
            papers = papers_list
        else:
            papers=self.papers

        introductions = [elt['Introduction'] if elt['Introduction'] else '' for elt in papers]
        return introductions

    def get_Abstracts(self, papers_list=[]):
        if papers_list:
            papers = papers_list
        else:
            papers=self.papers
        abstracts = [elt['Abstract'] if elt['Abstract'] else '' for elt in papers]
        return abstracts

    def get_Conclusions(self, papers_list=[]):
        if papers_list:
            papers = papers_list
        else:
            papers=self.papers
        conclusions = [elt['Conclusion'] if elt['Conclusion'] else '' for elt in papers]
        return conclusions

    def get_keywords(self, papers_list=[]):
        if papers_list:
            papers = papers_list
        else:
            papers=self.papers
        kwords = [elt['Keywords'] if elt['Keywords'] else '' for elt in papers]
        return kwords

    def doc2corpus(self, doc, remove_citation=True, replace_words=True, remove_urls=True, remove_emails=True):
        article = ArticleToProcess(doc, self.nlp)
        article.clean(remove_citation=remove_citation,
                      replace_words=replace_words,
                      remove_urls=remove_urls,
                      remove_emails=remove_emails)
        return ' '.join(article.tokens)

    def build_corpus(self, remove_citation=True, replace_words=True, remove_urls=True, remove_emails=True, save_chunks=False, path_save_chunks='', start_idx=0):
        iter=0
        for doc in tqdm(self.documents[start_idx:]):
            new_doc = self.doc2corpus(doc, remove_citation=remove_citation,
                                      replace_words=replace_words,
                                      remove_urls=remove_urls,
                                      remove_emails=remove_emails)
            self.corpus.append(new_doc)
            if save_chunks:
                if iter%400==0:
                    self.save_model(path_save_chunks)
                    print('  Saving corpus tfmodel - idx {}'.format(iter))

                iter+=1

    def update_docs_and_corpus(self, papers_updated,remove_citation=True, replace_words=True, remove_urls=True, remove_emails=True):
        papers_list = [papers_updated.elements[elt] for elt in papers_updated.elements]
        old_papers_fnames = [pap['file_name'] for pap in self.papers]
        new_papers_fnames = [pap['file_name'] for pap in papers_list if pap['file_name'] not in old_papers_fnames]
        new_papers = [papers_updated[fname] for fname in new_papers_fnames]
        new_documents = self.update_documents(new_papers)
        self.documents = self.documents + new_documents

        for doc in new_documents:
            new_doc = self.doc2corpus(doc, remove_citation=remove_citation,
                                      replace_words=replace_words,
                                      remove_urls=remove_urls,
                                      remove_emails=remove_emails)
            self.corpus.append(new_doc)

    def train(self, threshold=0):
        encodings = self.vectorizer.fit_transform(self.corpus).toarray()

        file_names = [pap['file_name'] for pap in self.papers]
        encodings_df = pd.DataFrame(encodings, columns=self.vectorizer.get_feature_names(),
                                      index=file_names)
        df = encodings_df.T[(encodings_df.T > threshold).any(1)]
        self.encodings = df.T
        # self.compute_cosine_scores()

    def compute_cosine_scores(self):
        self.cosine_scores = linear_kernel(self.encodings, self.encodings)

    def idx_to_filenames(self, list_idx):
        papers_concerned = list(map(self.papers.__getitem__, list_idx))
        papers_filenames = [elt['file_name'] for elt in papers_concerned]

        return papers_filenames

    def doc_in_docs(self, file_name, topn=5):
        self.compute_cosine_scores()
        for idx, pap in enumerate(self.papers):
            if pap['file_name'] == file_name:
                id_paper = idx
                break

        cos_score = np.array(self.cosine_scores[id_paper])
        result = self.most_similar(cos_score, topn)
        return result

    def most_similar(self, cosinus_score, topn, sentence=False):
        if sentence:
            cos_score = cosinus_score[0]
        else:
            cos_score = cosinus_score

        most_sims = np.argsort(cos_score)[::-1][1:(topn + 1)]
        paper_names = self.idx_to_filenames(most_sims)
        result = [(pap_name, cos_score[i]) for pap_name, i in zip(paper_names, most_sims) if cos_score[i]>0]
        return result

    def sentence_in_docs(self, sentence, topn=5):
        encodings_df = self.encodings
        new_doc = self.doc2corpus(sentence)

        tokens = new_doc.split()
        tokens_in_corpus = [tok for tok in tokens if tok in encodings_df.columns]

        # Get rows with all the query tokens
        df_all_tokens = encodings_df[(encodings_df[tokens_in_corpus]!=0).all(1)][tokens_in_corpus]
        df_all_tokens['mean'] = df_all_tokens.mean(axis=1)
        df_all_tokens = df_all_tokens.sort_values(by=['mean'], ascending=False)
        docs_with_all_tokens = [(doc, val) for doc, val in zip(list(df_all_tokens.index), df_all_tokens['mean']) if not np.isnan(val)]

        # Get rows with at least one of the query tokens
        filter_encodings_df = encodings_df.drop(list(df_all_tokens.index))
        df_one_token= filter_encodings_df[(filter_encodings_df[tokens_in_corpus]!=0).any(1)][tokens_in_corpus]
        df_one_token['mean'] = df_one_token.mean(axis=1)
        df_one_token = df_one_token.sort_values(by=['mean'], ascending=False)
        docs_with_one_tokens = [(doc, val) for doc, val in zip(list(df_one_token.index), df_one_token['mean']) if not np.isnan(val)]

        result = docs_with_all_tokens + docs_with_one_tokens
        return result[:topn]

    def get_in_path(self, result, topn=3,myfolder=''):
        new_topn=0
        file_names = [elt[0] for elt in result]
        result2=[]
        pap_names = [elt['file_name'] for elt in self.papers]
        for file_ in file_names:
            if new_topn<topn:
                idx_file = pap_names.index(file_)
                file_path = self.papers[idx_file]['pdf_path']
                dir_file = file_path.split('/')[-2]
                if myfolder == dir_file:
                    result2.append(file_)
                    new_topn+=1
        return result2

    def save_encodings(self,file_dir):
        self.encodings.to_parquet(file_dir, compression='gzip')

    def save_model(self, file_dir):
        with gzip.open(file_dir, "wb") as f:
            pickled = pickle.dumps(self.__dict__)
            optimized_pickle = pickletools.optimize(pickled)
            f.write(optimized_pickle)

    def load_encodings(self,file_dir):
        self.encodings = pd.read_parquet(file_dir)


    def load_model(self, file_dir):
        # if 'win' in platform:
        #     pathlib.PosixPath = pathlib.WindowsPath
        with gzip.open(file_dir, 'rb') as f:
            p = pickle.Unpickler(f)
            model =  p.load()
            self.__dict__ = model
            # self.__dict__= model.__dict__
        # filehandler = open(file_dir + '.tfmodel', 'rb')
        # self.__dict__ = pickle.load(filehandler)

