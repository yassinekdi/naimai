from sentence_transformers import SentenceTransformer, InputExample, losses, models, datasets
import random
import pandas as pd
import numpy as np
import spacy
from tqdm.notebook import  tqdm
import faiss

from paper2.constants.paths import naimai_data_path, training_data_path
from paper2.constants.nlp import nlp_vocab
from paper2.utils import load_papers_dict
from paper2.models.text_generation.query_generation import QueryGeneration

class Search_Model:
    def __init__(self, field,batch_size=16, n_epochs=10,
                 checkpoint='sentence-transformers/msmarco-distilbert-base-dot-prod-v3'):
        # training_data = pd.DataFrame({'File_name': [],'Queries': [..], 'Abstract': [..]})
        # naimai_data = pd.DataFrame({'filename': [],'doi': [..], 'Objectives reported': [..], 'database': [..]})
        self.checkpoint = checkpoint
        self.training_papers_dict= {}
        self.naimai_papers_dict= {}
        self.training_papers_df = None
        self.naimai_papers_df = None
        self.training_sbert_data_df = None
        self.model = None
        self.processed_data = None
        self.batch_size = batch_size
        self.n_epochs = n_epochs
        self.create_model()
        self.faiss_index = None
        self.nlp = spacy.load(nlp_vocab)
        self.field = field
        # self.test = []


    def load_data(self):
        self.training_papers_dict= load_papers_dict(path=training_data_path)
        self.naimai_papers_dict= load_papers_dict(path=naimai_data_path)

    def prepare_faiss_data(self):
        self.training_papers_df =pd.DataFrame([self.training_papers_dict[self.field][elt] for elt in self.training_papers_dict[self.field]])
        self.naimai_papers_df = pd.DataFrame([self.naimai_papers_dict[self.field][elt] for elt in self.naimai_papers_dict[self.field]])

    def prepare_sbert_data(self):
        percentage = .095
        training_data_papers = []
        naimai_data_papers = []
        for field in self.training_papers_dict.keys():
            papers_field_elements = list(self.training_papers_dict[field].keys())
            nb_of_samples = int(percentage * len(papers_field_elements))
            random_elts = random.sample(papers_field_elements, nb_of_samples)
            training_data_papers += [self.training_papers_dict[field][elt] for elt in random_elts]
            naimai_data_papers += [self.naimai_papers_dict[field][elt] for elt in random_elts]

        # preparing data for Sbert
        qgen = QueryGeneration(training_paper_dict=training_data_papers[0], nlp=self.nlp)
        training_data_dict={'filename': [],'Abstract': [], 'Queries': []}
        for pap in tqdm(training_data_papers):
            if len(pap['Abstract'].split())>10:
                qgen.paper = pap
                qgen.generate()
                for qry in qgen.queries:
                    training_data_dict['filename'].append(pap['file_name'])
                    training_data_dict['Abstract'].append(pap['Abstract'])
                    training_data_dict['Queries'].append(qry)


        self.training_sbert_data_df = pd.DataFrame(training_data_dict)

    def process_sbert_data(self):
        query, abstracts = self.training_sbert_data_df['Queries'].to_list(), self.training_sbert_data_df['Abstract'].to_list()
        train_examples = [InputExample(texts=[qry, parag]) for qry, parag in zip(query, abstracts)]
        random.shuffle(train_examples)
        self.processed_data = datasets.NoDuplicatesDataLoader(train_examples, batch_size=self.batch_size)

    def create_model(self):
        word_emb = models.Transformer(self.checkpoint)
        pooling = models.Pooling(word_emb.get_word_embedding_dimension())
        self.model = SentenceTransformer(modules=[word_emb, pooling], device='cuda')

    def train(self):
        train_loss = losses.MultipleNegativesRankingLoss(self.model)
        warmup_steps = int(len(self.processed_data) * self.n_epochs * 0.1)
        self.model.fit(train_objectives=[(self.processed_data, train_loss)], epochs=self.n_epochs,
                       warmup_steps=warmup_steps, show_progress_bar=True)

    def get_faiss_index(self,faiss_path_saving=''):
        self.prepare_faiss_data()
        to_encode = [title + '. '+ abstract for title,abstract in zip(self.training_papers_df.Abstract,self.training_papers_df.Title)]
        encoded_data = self.model.encode(to_encode)
        encoded_data = np.asarray(encoded_data.astype('float32'))
        self.faiss_index = faiss.IndexIDMap(faiss.IndexFlatIP(768))
        self.faiss_index.add_with_ids(encoded_data, np.array(range(len(self.training_papers_df))))

        if faiss_path_saving:
            print('faiss index saved')
            self.faiss.write_index(self.faiss_index, faiss_path_saving)

    def fetch_doc(self,df_idx):
        df_row = self.naimai_papers_df.iloc[df_idx, :]
        result = {}
        result['filename'] = df_row['file_name']
        result['reported'] = df_row['Objectives_reported']
        return result

    def search(self,query, top_k):
        query_vector = self.model.encode([query])
        top_k = self.faiss_index.search(query_vector, top_k)
        top_k_ids = top_k[1].tolist()[0]
        top_k_ids = list(np.unique(top_k_ids))
        results = [self.fetch_doc(idx) for idx in top_k_ids]
        return results


    def fine_tune(self,model_path_saving='',faiss_path_saving=''):
        print('>> Data processing ..')
        self.load_data()
        self.prepare_sbert_data()
        self.process_sbert_data()

        print('>> Training...')
        self.train()

        if model_path_saving:
            print('>> Model saving..')
            self.model.save(model_path_saving)
        print('>> Getting faiss index..')
        self.get_faiss_index(faiss_path_saving=faiss_path_saving)
