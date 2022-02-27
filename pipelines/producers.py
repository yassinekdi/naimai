from naimai.classifiers import Objective_classifier
from naimai.constants.nlp import max_len_objective_sentence, nlp_vocab
from naimai.constants.paths import path_objective_classifier, path_produced, path_dispatched
from naimai.constants.regex import regex_objectives, regex_filtered_words_obj
from naimai.utils.regex import clean_objectives
from naimai.utils.general import save_gzip, load_gzip
from naimai.models.text_generation.paper2reported import Paper2Reported
from naimai.models.papers_classification.semantic_search import Search_Model

import os
import re
import spacy
from tqdm.notebook import tqdm
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class Paper_Producer:
    '''
    Takes formatted paper & transforms it to production paper, in dict format :
    {'doi': xx, 'reported':xx, 'year': xx, 'database': xx}
    '''
    def __init__(self, paper, paper_name='', obj_classifier_model=None, nlp=None):
        self.paper_name = paper_name
        self.paper = paper
        self.objectives_with_regex = []
        self.objectives_with_classifier = []
        self.objectives = []
        self.objectives_reported = []
        self.obj_classifier_model = obj_classifier_model
        self.nlp = nlp
        self.production_paper = {}

    def load_objective_model(self):
        if not self.obj_classifier_model:
            print('>> Loading obj model..')
            self.obj_classifier_model = Objective_classifier(dir=path_objective_classifier)

    def get_objectives_with_regex(self):
        objective_phrases = list(set(re.findall(regex_objectives, self.paper['Abstract'], flags=re.I)))
        self.objectives_with_regex = clean_objectives(objective_phrases)

    def get_objectives_with_classifier(self, add_sentences=[]):
        if self.objectives_with_regex:
            list_sentences = self.objectives_with_regex + add_sentences
        else:
            list_sentences = self.paper['Abstract'].split('.') + add_sentences
        list_sentences = [elt for elt in list_sentences if len(elt.split()) < max_len_objective_sentence]
        objectives = self.obj_classifier_model.predict(list_sentences)
        self.objectives_with_classifier = [obj for obj in objectives if
                                           not re.findall(regex_filtered_words_obj, obj, flags=re.I)]

    def get_objective_paper(self, add_sentences=[]):
        self.load_objective_model()
        self.get_objectives_with_regex()
        self.get_objectives_with_classifier(add_sentences=add_sentences)
        if self.objectives_with_classifier:
            self.objectives = self.objectives_with_classifier
        else:
            self.objectives = self.objectives_with_regex

    def report_objectives(self):
        if not self.nlp:
            print('>> Loading nlp..')
            self.nlp = spacy.load(nlp_vocab)
        review = Paper2Reported(paper=self.paper,
                                paper_name=self.paper_name,
                                paper_objectives=self.objectives,
                                nlp=self.nlp,
                                )
        review.generate()
        review.choose_objective()
        if review.list_reported:
            self.objectives_reported = review.reported_objective

    def format_paper(self):
        formatted_paper = {"doi": self.paper['doi'],
                           "reported": self.objectives_reported,
                           "year": self.paper['year'],
                           "database": self.paper['database']}
        self.production_paper = formatted_paper

    def produce_paper(self, add_sentences=[]):
        self.get_objective_paper(add_sentences=add_sentences)
        self.report_objectives()
        self.format_paper()


class Field_Producer:
    '''
    Takes formatted papers of a field and transform them to a produced paper using Paper Producer obj
    '''
    def __init__(self, field, obj_classifier_model=None, nlp=None, encoder=None):
        self.field = field
        self.field_papers = {}
        self.obj_classifier_model = obj_classifier_model
        self.nlp = nlp
        self.production_field = {}
        self.field_index = None
        self.encoder = encoder

    def load_objective_model(self):
        if not self.obj_classifier_model:
            print(' - obj model..')
            self.obj_classifier_model = Objective_classifier(dir=path_objective_classifier)

    def load_nlp(self):
        if not self.nlp:
            print(' - nlp..')
            self.nlp = spacy.load(nlp_vocab)

    def load_encoder(self, path):
        print(' - encoder..')
        path = os.path.join(path_produced, self.field, 'search_model')
        if os.path.isdir(path):
            print('   - encoder exists, loading encoder..')
            self.encoder = SentenceTransformer(path)
        else:
            print('   - no encoder.. you need to fine tune..')

    def load_field_papers(self):
        print(' - field paper..')
        path = os.path.join(path_dispatched,self.field,"all_papers")
        self.field_papers = load_gzip(path)

    def produce_paper(self, paper, paper_name):
        pap_producer = Paper_Producer(paper=paper, paper_name=paper_name,
                                      obj_classifier_model=self.obj_classifier_model, nlp=self.nlp)
        pap_producer.produce_paper(add_sentences=paper['highlights'])
        prod = pap_producer.production_paper
        if prod['reported']:
            return prod
        else:
            with open('reported_pbs.txt', 'a') as f:
                f.write(
                    'problem with reporting obj in paper : {} - dbase : {} \n\n'.format(paper_name, paper['database']))
            return

    def get_field_index(self):
        fnames = list(self.production_field.keys())
        to_encode = [self.field_papers[fn]['Title'] + ' '+ self.field_papers[fn]['Abstract'] for fn in fnames]
        encoded_fields = self.encoder.encode(to_encode)
        encoded_fields = np.asarray(encoded_fields.astype('float32'))
        self.field_index = faiss.IndexIDMap(faiss.IndexFlatIP(768))
        self.field_index.add_with_ids(encoded_fields, np.array(range(len(to_encode))))

    def fine_tune_model(self, size_data,batch_size,n_epochs=10):
        smodel = Search_Model(field=self.field,batch_size=batch_size,n_epochs=n_epochs)
        smodel.fine_tune(size_data=size_data)
        self.encoder = smodel.model

    def save_model(self):
        path = os.path.join(path_produced, self.field, 'search_model')
        self.encoder.save(path)


    def produce(self,save_papers=False,save_field_index=False):
        print('>> Loading..')
        self.load_objective_model()
        self.load_nlp()
        self.load_encoder()
        if self.encoder:
            self.load_field_papers()
            print(' ')
            print('>> Producing (objective+format)..')
            for fname in tqdm(self.field_papers):
                pap = self.field_papers[fname]
                production_paper = self.produce_paper(paper=pap, paper_name=fname)
                if production_paper:
                    self.production_field[fname] = production_paper
            print(' ')
            print('>> Computing Faiss Index..')
            self.get_field_index()
            print(' ')
            if save_papers:
                print('>> Saving papers..')
                self.save_papers()

            if save_field_index:
                print('>> Saving field index..')
                self.save_field_index()
            print(' ')
            print('>> Done!')
            print('>> Papers with reported obj problems are stored in reported_pbs.txt')

    def save_field_index(self):
        path = os.path.join(path_produced, self.field, 'encodings.index')
        faiss.write_index(self.field_index, path)

    def save_papers(self):
        path = os.path.join(path_produced, self.field, 'all_papers')
        save_gzip(path, self.production_field)
