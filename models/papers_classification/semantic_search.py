from tqdm.notebook import tqdm
from naimai.constants.paths import path_dispatched
from naimai.pipelines.zones import Production_Zone
from naimai.models.text_generation.query_generation import QueryGeneration
import torch

import pandas as pd
import spacy
import os
import random
from sentence_transformers import SentenceTransformer, InputExample, losses, models, datasets


class Search_Model:
  def __init__(self, field: str,papers: dict,batch_size=16,n_epochs=10,checkpoint='sentence-transformers/msmarco-distilbert-base-dot-prod-v3'):
    self.field = field
    self.batch_size = batch_size
    self.n_epochs = n_epochs
    self.checkpoint = checkpoint
    self.training_data_df = None
    self.model = None
    self.papers = papers

  def prepare_data(self):
    keys = list(self.papers.keys())
    messages = [self.papers[fname]['messages'] for fname in keys] 
    messages = [elt for elt2 in messages for elt in elt2]
    titles = [self.papers[fname]['title'] for fname in keys if 'title' in self.papers[fname]]

    sentences = messages+titles
    qgen = QueryGeneration(nb_queries=2)
    training_data_dict={'sentences': [], 'queries': []}
    for sentence in tqdm(sentences):
        if len(sentence.split())>5:
            queries = qgen.from_message(sentence)
            if queries:
                for qry in queries:
                    training_data_dict['sentences'].append(sentence)
                    training_data_dict['queries'].append(qry)

    self.training_data_df = pd.DataFrame(training_data_dict)

  def process_data(self):
    query, sentences = self.training_data_df['queries'].to_list(), self.training_data_df['sentences'].to_list()
    train_examples = [InputExample(texts=[qry, parag]) for qry, parag in zip(query, sentences)]
    random.shuffle(train_examples)
    self.processed_data = datasets.NoDuplicatesDataLoader(train_examples, batch_size=self.batch_size)

  def create_model(self):
    word_emb = models.Transformer(self.checkpoint)
    pooling = models.Pooling(word_emb.get_word_embedding_dimension())
    if torch.cuda.is_available():
      print('  >> GPU Used in search model !')
      self.model = SentenceTransformer(modules=[word_emb, pooling], device='cuda')
    else:
      print('  >> No GPU used in search model..')
      self.model = SentenceTransformer(modules=[word_emb, pooling])



  def train(self):

    train_loss = losses.MultipleNegativesRankingLoss(self.model)
    warmup_steps = int(len(self.processed_data) * self.n_epochs * 0.1)
    self.model.fit(train_objectives=[(self.processed_data, train_loss)], epochs=self.n_epochs,
                    warmup_steps=warmup_steps, show_progress_bar=True)
  def fine_tune(self,model_path_saving=''):
    print('>> Preparing data..')
    self.prepare_data()
    self.process_data()

    print('>> Modelling..')

    if not self.model:
      self.create_model()
    else:
      print('>> Training the loaded encoding model  .. ')
      self.model.to('cuda')
    self.train()

    if model_path_saving:
      print('>> Model saving..')
      self.model.save(model_path_saving)
    print('Done!')
