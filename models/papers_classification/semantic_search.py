from tqdm.notebook import tqdm
from naimai.constants.paths import path_dispatched
from naimai.constants.nlp import nlp_vocab
from naimai.utils.general import load_gzip
from naimai.models.text_generation.query_generation import QueryGeneration
import torch

import pandas as pd
import spacy
import os
import random
from sentence_transformers import SentenceTransformer, InputExample, losses, models, datasets


class Search_Model:
  def __init__(self, field,papers,batch_size=16,n_epochs=10,checkpoint='sentence-transformers/msmarco-distilbert-base-dot-prod-v3'):
    self.field = field
    self.papers = {}
    self.batch_size = batch_size
    self.n_epochs = n_epochs
    self.checkpoint = checkpoint
    self.nlp = spacy.load(nlp_vocab)
    self.training_data_df = None
    self.model = None
    self.load_papers(papers)

  def load_papers(self, papers):
    if papers:
      self.papers = papers
    else:
      print('>> Loading papers..')
      path = os.path.join(path_dispatched,self.field,"all_papers")
      self.papers = load_gzip(path)
      print('Len data : ', len(self.papers))


  def prepare_data(self):
    keys = list(self.papers.keys())
    training_data_papers = [self.papers[key] for key in keys]

    qgen = QueryGeneration(training_paper_dict=training_data_papers[0], nlp=self.nlp)
    training_data_dict={'Abstract': [], 'Queries': []}
    for pap in tqdm(training_data_papers):
        if len(pap['Abstract'].split())>10:
            qgen.paper = pap
            qgen.generate()
            if qgen.queries:
                for qry in qgen.queries:
                    training_data_dict['Abstract'].append(pap['Abstract'])
                    training_data_dict['Queries'].append(qry)

    self.training_data_df = pd.DataFrame(training_data_dict)

  def process_data(self):
    query, abstracts = self.training_data_df['Queries'].to_list(), self.training_data_df['Abstract'].to_list()
    train_examples = [InputExample(texts=[qry, parag]) for qry, parag in zip(query, abstracts)]
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
