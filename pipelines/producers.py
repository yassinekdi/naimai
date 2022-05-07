from naimai.models.papers_classification.obj_classifier import Objective_classifier
from naimai.models.papers_classification.bomr_classif.ner_classifier import NER_BOMR_classifier
from naimai.models.papers_classification.bomr_classif.omr_segmentors import segment
from naimai.constants.nlp import nlp_vocab
from naimai.constants.regex import regex_not_converted2
from naimai.utils.regex import get_ref_url
from naimai.constants.paths import path_produced, path_dispatched, path_bomr_classifier
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
    Takes formatted paper 'fname' & transforms it to production paper, a dict of 3 differents dicts (obj,meth and res) :
    {'objectives': {'website': xx,
             'year':xx,
             'database': xx,
             'authors': et al,
             'message': xx,
             'reported': xx,
             'title': xx,
             'journal': xx},
     'methods': {'message': xx},
     'results': {'message': xx}
     }
    When no objective is found after segmentation, we correct by looking for it in results, otherwise in methods.
    '''

    def __init__(self, paper, paper_name='', obj_classifier=None, bomr_classifier=None, nlp=None):
        self.paper_name = paper_name
        self.paper = paper
        self.authors = ''
        self.bomr_classifier = None
        self.obj_classifier = None
        self.nlp = None
        self.production_paper = {}
        self.omr = {'objectives': [], 'methods': [], 'results': [], 'other': []}
        self.reported = ''

        self.load_obj_classifier(obj_classifier)
        self.load_bomr_classifier(bomr_classifier)
        self.load_nlp(nlp)

    def load_obj_classifier(self, obj_classifier):
        if obj_classifier:
            self.obj_classifier = obj_classifier
        else:
            print('>> Loading obj classifier..')
            self.obj_classifier = Objective_classifier()

    def load_bomr_classifier(self, bomr_classifier):
        if bomr_classifier:
            self.bomr_classifier = bomr_classifier
        else:
            print('>> Loading bomr classifier..')
            self.bomr_classifier = NER_BOMR_classifier(load_model=True, path_model=path_bomr_classifier,
                                                       predict_mode=True)

    def clean_abstract(self,text) -> str:
        '''
        clean abstract by removing the non converted expressions
        :param text:
        :return:
        '''
        return re.sub(regex_not_converted2,'',text)

    def load_nlp(self, nlp):
        if nlp:
            self.nlp = nlp
        else:
            print('>> Loading nlp..')
            self.nlp = spacy.load(nlp_vocab)

    def get_omr_dict(self) -> dict:
        '''
        get {'obj': [xx,yy], 'methods': [xx,yy], 'results': [zz,ff]}
        :return:
        '''
        abstract = self.clean_abstract(self.paper['Abstract'])
        segments, sentences, _, _ = segment(text=abstract,
                                            obj_clf=self.obj_classifier,
                                            bomr_clf=self.bomr_classifier,
                                            summarize=True,
                                            check_bg=True,
                                            visualize_=False,
                                            )
        for stc_idx in segments:
            label = segments[stc_idx]
            self.omr[label].append(sentences[stc_idx])

    def report(self) -> str:
        '''
        report objectives, else report results, else methods
        :return:
        '''
        objectives, methods, results = self.omr['objectives'], self.omr['methods'], self.omr['results']
        if objectives:
            messages_reported = self.report_messages(objectives)
            self.reported = messages_reported
        if methods and not self.reported:
            messages_reported = self.report_messages(methods)
            self.reported = messages_reported
        if results and not self.reported:
            messages_reported = self.report_messages(results)
            self.reported = messages_reported

    def report_messages(self, messages: list) -> list:
        messages_reported = []
        review = Paper2Reported(paper=self.paper,
                                paper_name=self.paper_name,
                                messages=messages,
                                nlp=self.nlp,
                                )
        review.generate()
        review.choose_objective()
        self.authors = review.processed_authors
        if review.list_reported:
            messages_reported = review.reported_objective
        return messages_reported

    def format_paper(self) -> dict:
        journal = self.paper['Journal']
        if journal and re.findall('[a-zA-Z]', journal):
            journal = re.sub('^nd|ISSN','',journal).strip()
        else:
            journal=''

        objectives = {"website": get_ref_url(self.paper),
                      "year": self.paper['year'],
                      "database": self.paper['database'],
                      "message": self.omr['objectives'],
                      "reported": self.reported,
                      "title": self.paper['Title'],
                      "journal": journal,
                      "authors": self.authors}
        methods = {"message": self.omr['methods']}
        results = {"message": self.omr['results']}
        self.production_paper = {'objectives': objectives, "methods": methods, "results": results}

    def produce_paper(self):
        self.get_omr_dict()
        objectives, methods, results = self.omr['objectives'], self.omr['methods'], self.omr['results']
        if objectives or methods or results:
            self.report()
            self.format_paper()


class Field_Producer:
    '''
    1 Takes formatted papers of a field and transform them to a produced paper using Paper Producer obj
    2 Can finetune search model to get the field encoder
    3 Compute field Faiss index
    '''
    def __init__(self, field, obj_classifier=None,bomr_classifier=None, nlp=None,
                 encoder=None, field_papers=None):
        self.field = field
        self.field_papers = {}
        self.obj_classifier = None
        self.bomr_classifier = None
        self.nlp = None
        self.encoder = None

        self.production_field = {}
        self.field_index = None

        self.load_obj_classifier(obj_classifier)
        self.load_bomr_classifier(bomr_classifier)
        self.load_nlp(nlp)
        self.load_encoder(encoder)
        self.load_field_papers(field_papers)

    def load_obj_classifier(self, obj_classifier):
        if obj_classifier:
            self.obj_classifier = obj_classifier
        else:
            print('>> Loading obj classifier..')
            self.obj_classifier = Objective_classifier()

    def load_bomr_classifier(self, bomr_classifier):
        if bomr_classifier:
            self.bomr_classifier = bomr_classifier
        else:
            print('>> Loading bomr classifier..')
            self.bomr_classifier = NER_BOMR_classifier(load_model=True, path_model=path_bomr_classifier,
                                                       predict_mode=True)

    def load_nlp(self, nlp):
        if nlp:
            self.nlp = nlp
        else:
            print('>> Loading nlp..')
            self.nlp = spacy.load(nlp_vocab)

    def load_encoder(self, encoder):
        if encoder:
          self.encoder = encoder
        else:
          path = os.path.join(path_produced, self.field, 'search_model')
          if os.path.isdir(path):
            print('>> Loading field encoder..')
            self.encoder = SentenceTransformer(path)
          else:
              print('>> No field encoder.. You need to fine tune !')

    def load_field_papers(self, field_papers):
      if field_papers:
        self.field_papers = field_papers
      else:
        print('>> Loading field papers..')
        path = os.path.join(path_dispatched,self.field,"all_papers")
        self.field_papers = load_gzip(path)
        print(' >> Len papers: ', len(self.field_papers))

    def produce_paper(self, paper: dict, paper_name: str) -> dict:
        '''
        produce paper using Paper_Producer : turns paper 'fname' to 'fname_objectives',
        'fname_methods' and 'fname_results'
        :param paper:
        :param paper_name:
        :return:
        '''
        pap_producer = Paper_Producer(paper=paper, paper_name=paper_name,
                              obj_classifier=self.obj_classifier,
                              bomr_classifier=self.bomr_classifier,
                              nlp=self.nlp)

        pap_producer.produce_paper()
        prod = pap_producer.production_paper
        if prod:
          self.production_field[paper_name+'_objectives'] = prod['objectives']
          self.production_field[paper_name+'_methods'] = prod['methods']
          self.production_field[paper_name+'_results'] = prod['results']

    def txt_to_encode(self,fname: str)-> str:
      '''
      get what text to encode from produced paper (element of self.production_field)
      :param fname:
      :return:
      '''
      if '_objectives' in fname:
        return self.production_field[fname]['title']+ ' ' + self.production_field[fname]['message']
      else:
        return self.production_field[fname]['message']

    def get_field_index(self):
        print('>> Computing Faiss Index..')
        fnames = list(self.production_field.keys())
        to_encode = [self.txt_to_encode[fn] for fn in fnames]
        encoded_fields = self.encoder.encode(to_encode)
        encoded_fields = np.asarray(encoded_fields.astype('float32'))
        self.field_index = faiss.IndexIDMap(faiss.IndexFlatIP(768))
        self.field_index.add_with_ids(encoded_fields, np.array(range(len(to_encode))))
        print(' ')

    def fine_tune_field_encoder(self, size_data: int,save_model: bool,batch_size=16,n_epochs=10):
        '''
        finetune search model using a size 'size_data' from field_papers
        :param size_data:
        :param save_model:
        :param batch_size:
        :param n_epochs:
        :return:
        '''
        smodel = Search_Model(field=self.field,papers=self.field_papers,batch_size=batch_size,n_epochs=n_epochs)
        smodel.fine_tune(size_data=size_data)
        self.encoder = smodel.model
        if save_model:
          self.save_model()

    def save_model(self):
        path = os.path.join(path_produced, self.field, 'search_model')
        self.encoder.save(path)

    def produce_field_papers(self):
      print('>> Producing field papers..')
      for fname in tqdm(self.field_papers):
          pap = self.field_papers[fname]
          self.produce_paper(paper=pap, paper_name=fname)
      print(' ')

    def produce(self,save_papers=False,save_field_index=False):
        if self.encoder:
            # produce field papers
            self.produce_field_papers()

            #compute Faiss index
            self.get_field_index()

            #save
            if save_papers:
                print('>> Saving papers..')
                self.save_papers()

            if save_field_index:
                print('>> Saving field index..')
                self.save_field_index()
            print(' ')
            print('>> Done!')
        else:
            print('>> The production is not done (no field encoder). You need to fine tune.')

    def save_field_index(self):
        path = os.path.join(path_produced, self.field, 'encodings.index')
        faiss.write_index(self.field_index, path)

    def save_papers(self):
        path = os.path.join(path_produced, self.field, 'all_papers')
        save_gzip(path, self.production_field)
