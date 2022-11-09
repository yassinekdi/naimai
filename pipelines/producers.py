'''
- Paper_Producer Class : takes a paper (as a dictionary) and structures its abstract into objectives, methods and results.

- Field_Producer Class : takes a field (directory with papers of the same field) and produces all the papers using Paper_Producer object.

- Custom_Producer Class :
'''

from naimai.models.papers_classification.obj_classifier import Objective_classifier
from naimai.models.papers_classification.bomr_classif.ner_classifier import NER_BOMR_classifier
from naimai.models.papers_classification.bomr_classif.omr_segmentors import segment
from naimai.constants.nlp import nlp_vocab
from naimai.constants.regex import regex_not_converted2
from naimai.utils.regex import get_ref_url
from naimai.constants.paths import path_produced, path_dispatched, path_bomr_classifier
from naimai.utils.general import save_gzip, load_gzip, load_gzip_and_update
from naimai.models.text_generation.paper2reported import Paper2Reported
from naimai.pipelines.zones import Production_Zone
from naimai.models.papers_classification.semantic_search import Search_Model
import os
import re
import spacy
import random
from tqdm.notebook import tqdm
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

D = 768
vecs = faiss.IndexFlatIP(D)
ncentroids = 256
code_size = 32


class Paper_Producer:
    '''
    Takes formatted paper 'fname' & transforms it to production paper, a dict of 3 differents dicts (obj,meth and res) :
    {'objectives': {'website': xx,
             'year':xx,
             'database': xx,
             'authors': et al,
             'messages': xx,
             'reported': xx,
             'title': xx,
             'journal': xx,
             ' numCitedBy': xx},
     'methods': {'messages': xx,
                'year': xx,
                ' numCitedBy': xx},
     'results': {'messages': xx,
                'year': xx,
                ' numCitedBy': xx}
     }
    When no objective is found after segmentation, we correct by looking for it in results, otherwise in methods.
    '''

    def __init__(self, paper: dict, paper_name='', obj_classifier=None, bomr_classifier=None, nlp=None):
        self.paper_name = paper_name
        self.paper = paper
        self.authors = ''
        self.bomr_classifier = None
        self.obj_classifier = None
        self.nlp = None
        self.production_paper = {}
        self.omr = {'objectives': [], 'methods': [], 'results': [], 'other': []}
        self.reported = ''
        self.smodel = None

        self.load_obj_classifier(obj_classifier)
        self.load_bomr_classifier(bomr_classifier)
        self.load_nlp(nlp)

    def load_obj_classifier(self, obj_classifier):
        '''
        Load the objective classifier: model that selects the objective sentence in the abstract.
        :param obj_classifier:
        :return:
        '''
        if obj_classifier:
            self.obj_classifier = obj_classifier
        else:
            print('>> Loading obj classifier..')
            self.obj_classifier = Objective_classifier()

    def load_bomr_classifier(self, bomr_classifier):
        '''
        Load the bomr classifier, the model that structures the abstract into bibliography, objectives, methods
        and results.
        :param bomr_classifier:
        :return:
        '''
        if bomr_classifier:
            self.bomr_classifier = bomr_classifier
        else:
            print('>> Loading bomr classifier..')
            self.bomr_classifier = NER_BOMR_classifier(load_model=True, path_model=path_bomr_classifier,
                                                       predict_mode=True)

    def clean_abstract(self,text: str) -> str:
        '''
        clean abstract by removing the non converted expressions
        :param text:
        :return:
        '''
        return re.sub(regex_not_converted2,'',text)

    def load_nlp(self, nlp):
        '''
        Load nlp model (spaCy)
        :param nlp:
        :return:
        '''
        if nlp:
            self.nlp = nlp
        else:
            print('>> Loading nlp..')
            self.nlp = spacy.load(nlp_vocab)

    def get_omr_dict(self):
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
                                            nlp = self.nlp,
                                            )
        for stc_idx in segments:
            label = segments[stc_idx]
            self.omr[label].append(sentences[stc_idx])

    def report(self):
        '''
        report objectives (write objective sentences in reported speech), else report results, else methods
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
        '''
        takes the messages and transform them into reported speech format.
        :param messages: list of sentences
        :return:
        '''
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

    def format_paper(self):
        '''
        Format the paper (in self.paper) and structures it into a dictionary with objectives, methods and results.
        :return:
        '''
        journal = self.paper['Journal']
        if journal and re.findall('[a-zA-Z]', journal):
            journal = re.sub('^nd|ISSN','',journal).strip()
        else:
            journal=''

        if self.paper['year']:
            year = int(self.paper['year'])
        else:
            year = self.paper['year']
            print('Year problem in paper: ', self.paper_name)
        if 'all_authors' in self.paper:
            objectives = {"website": get_ref_url(self.paper),
                      "year": year,
                      "database": self.paper['database'],
                      "messages": self.omr['objectives'],
                      "reported": self.reported,
                      "title": self.paper['Title'],
                      'numCitedBy': self.paper['numCitedBy'],
                      "journal": journal,
                      "authors": self.authors,
                      'allauthors': self.paper['allauthors']}
        else:
            objectives = {"website": get_ref_url(self.paper),
                      "year": year,
                      "database": self.paper['database'],
                      "messages": self.omr['objectives'],
                      "reported": self.reported,
                      "title": self.paper['Title'],
                      'numCitedBy': self.paper['numCitedBy'],
                      "journal": journal,
                      "authors": self.authors}
        methods = {"messages": self.omr['methods'],"numCitedBy": self.paper['numCitedBy'],"year": year}
        results = {"messages": self.omr['results'],"numCitedBy": self.paper['numCitedBy'],"year": year}
        self.production_paper = {'objectives': objectives, "methods": methods, "results": results}

    def produce_paper(self):
        '''
        Produce the paper by reporting its objectives sentence (in reported speech format) and formatting it
        (finding the objectives, methods and results)
        :return:
        '''
        self.get_omr_dict()
        objectives, methods, results = self.omr['objectives'], self.omr['methods'], self.omr['results']
        if objectives or methods or results:
            self.report()
            self.format_paper()


class Field_Producer:
    '''
    1 Takes formatted papers of a all_papers in a field (dispatched zone) and transform them into a produced all_paper using Paper Producer obj
    2 Can finetune search model to get the field encoder
    3 Compute field Faiss index
    '''
    def __init__(self, field, all_papers='', ref_fields= [], obj_classifier=None, bomr_classifier=None, nlp=None, encoder=None, field_papers=None, idx_start=0, idx_finish=-1, load_dispatched_field_papers=True, load_obj_classifier=True,
                 load_bomr_classifier=True, load_nlp=True, load_field_encoder=True):
        self.field = field
        self.dispatched_field_papers = {}
        self.obj_classifier = None
        self.bomr_classifier = None
        self.nlp = None
        self.encoder = None
        self.smodel = None
        self.ref_fields = ref_fields
        self.papers_ref_fields = {} # fields used to check if same paper is already produced

        self.produced_field_papers = {}
        self.field_index = None
        self.produce_only_fnames=False
        self.all_papers = all_papers
        if load_obj_classifier:
            self.load_obj_classifier(obj_classifier)
        if load_bomr_classifier:
            self.load_bomr_classifier(bomr_classifier)
        if load_nlp:
            self.load_nlp(nlp)
        if load_field_encoder:
            self.load_encoder(encoder)
        if load_dispatched_field_papers:
            self.load_dispatched_field_papers_(field_papers=field_papers, all_papers=all_papers, idx_start=idx_start, idx_finish=idx_finish)
        self.idx_finish = idx_finish
        self.idx_start= idx_start
        if idx_finish!=-1 or idx_start!=0:
            self.extracted=True
        else:
            self.extracted=False


    def load_obj_classifier(self, obj_classifier):
        '''
        Load the objective classifier: model that selects the objective sentence in the abstract.
        :param obj_classifier:
        :return:
        '''
        if obj_classifier:
            self.obj_classifier = obj_classifier
        else:
            print('>> Loading obj classifier..')
            self.obj_classifier = Objective_classifier()

    def load_bomr_classifier(self, bomr_classifier):
        '''
        Load the bomr classifier, the model that structures the abstract into bibliography, objectives, methods
        and results.
        :param bomr_classifier:
        :return:
        '''
        if bomr_classifier:
            self.bomr_classifier = bomr_classifier
        else:
            print('>> Loading bomr classifier..')
            self.bomr_classifier = NER_BOMR_classifier(load_model=True, path_model=path_bomr_classifier,
                                                       predict_mode=True)

    def load_nlp(self, nlp):
        '''
        Load nlp model (spaCy)
        :param nlp:
        :return:
        '''
        if nlp:
            self.nlp = nlp
        else:
            print('>> Loading nlp..')
            self.nlp = spacy.load(nlp_vocab)

    def load_encoder(self, encoder):
        '''
        Load the bert encoder, finetuned on the field produced papers.
        :param nlp:
        :return:
        '''
        if encoder:
          self.encoder = encoder
        else:
          path = os.path.join(path_produced, self.field, 'search_model')
          if os.path.isdir(path):
            print('>> Loading field encoder..')
            self.encoder = SentenceTransformer(path)
          else:
              print('>> No field encoder.. You need to fine tune !')

    def load_dispatched_field_papers_(self, field_papers: str, all_papers: str, idx_start=0, idx_finish=-1):
      '''
      Load field papers from dispatched zone
      :param field_papers: field of papers
      :param all_papers: all_papers name
      :param idx_start:
      :param idx_finish:
      :return:
      '''
      if field_papers:
          keys = list(field_papers)[idx_start:idx_finish]
          self.dispatched_field_papers = {elt: field_papers[elt] for elt in keys}
      else:
        print('>> Loading field papers : ', all_papers)
        path = os.path.join(path_dispatched,self.field, all_papers)
        self.dispatched_field_papers = load_gzip(path)
        keys = list(self.dispatched_field_papers)[idx_start:idx_finish]
        self.dispatched_field_papers = {elt: self.dispatched_field_papers[elt] for elt in keys}
        print(' >> Len papers: ', len(self.dispatched_field_papers))


    def get_papers_ref_fields(self):
        '''
        get papers of reference fields
        :param fields:
        :return:
        '''
        for field in self.ref_fields:
            path_papers = os.path.join(path_produced,field,self.all_papers)
            papers_field = load_gzip(path_papers)
            self.papers_ref_fields.update(papers_field)

        self.papers_ref_fields['fnames'] = [fname for fname in self.papers_ref_fields]


    def paper_in_refs(self,dispatched_paper_name: str) -> bool:
        '''
        check if paper exists in refs
        :param dispatched_paper_name:
        :return:
        '''
        for fname in self.papers_ref_fields:
            if dispatched_paper_name in fname:
                return True
        return False

    def get_in_refs_papers(self,dispatched_paper_name: str) -> dict:
        '''
        check if the same paper was produced in other fields, and return dictionary with omr if the paper exists
        :return:
        '''
        omr = {}
        if not self.papers_ref_fields:
            self.get_papers_ref_fields()

        if self.paper_in_refs(dispatched_paper_name):
            for fname in self.papers_ref_fields:
                if dispatched_paper_name in fname:
                    omr[fname] = self.papers_ref_fields[fname]
        return omr

    def produce_paper(self, paper: dict, paper_name: str) -> dict:
        '''
        produce paper using Paper_Producer : turns paper 'fname' to 'fname_objectives',
        'fname_methods' and 'fname_results'
        :param paper:
        :param paper_name:
        :return:
        '''
        prod = self.get_in_refs_papers(paper_name)
        if prod:
            self.produced_field_papers.update(prod)
        else:
            pap_producer = Paper_Producer(paper=paper, paper_name=paper_name,
                                  obj_classifier=self.obj_classifier,
                                  bomr_classifier=self.bomr_classifier,
                                  nlp=self.nlp)

            pap_producer.produce_paper()
            prod = pap_producer.production_paper

            if prod:
              self.produced_field_papers[paper_name+'_objectives'] = prod['objectives']
              self.produced_field_papers[paper_name+'_methods'] = prod['methods']
              self.produced_field_papers[paper_name+'_results'] = prod['results']

    def txt_to_encode(self,fname: str,papers_dict=None)-> str:
      '''
      get what text to encode from papers_dict (element of self.produced_field_papers)
      :param fname:
      :return:
      '''
      if not papers_dict:
          papers_dict = self.produced_field_papers

      messages = ' '.join(papers_dict[fname]['messages'])
      if '_objectives' in fname:
        return papers_dict[fname]['title']+ ' ' + messages
      else:
        return messages

    def gather_production_papers(self,papers_name='',save=True):
        '''
        load all_papers chunks (produced between 2 indices for same database) and gather them in the same dictionary
        :return: dictionary
        '''
        path_produced_papers = os.path.join(path_produced, self.field)
        all_files = os.listdir(path_produced_papers)

        if papers_name:
            new_fnames = {papers_name: [elt for elt in all_files if papers_name in elt]}
            disp_zone_fnames = [papers_name,]

        else:
            disp_zone_path = os.path.join(path_dispatched, self.field)
            disp_zone_fnames = os.listdir(disp_zone_path)

            all_files = os.listdir(path_produced_papers)

            new_fnames = {fname: [elt for elt in all_files if re.findall(fname + '_\d+', elt)] for fname in disp_zone_fnames}

        for fname in disp_zone_fnames:
            if not new_fnames[fname]:
                new_fnames[fname] = [fname]

        all_papers = {}
        print('>> Loading for updating..')
        for fname in new_fnames:
            fnames = new_fnames[fname]
            path_fnames = [os.path.join(path_produced_papers,fname) for fname in fnames]
            all_papers[fname]= load_gzip_and_update(path_fnames)

        if save:
            print('>> Saving..')
            for fname in all_papers:
                path = os.path.join(path_produced_papers,fname)
                print('  Saving : ', fname)
                save_gzip(path,all_papers[fname])
                for paper in all_papers[fname]:
                    self.produced_field_papers[paper]= all_papers[fname][paper]

    def remove_chunks(self,all_papers_name):
        '''
        remove all_papers chunks (produced between 2 indices for same database)
        :return:
        '''
        path_produced_papers = os.path.join(path_produced, self.field)
        all_files = os.listdir(path_produced_papers)

        chunks_fname = [elt for elt in all_files if re.findall(all_papers_name + '_\d+', elt)]
        paths = [os.path.join(path_produced_papers,elt) for elt in chunks_fname]
        for path in paths:
            os.remove(path)

    def get_field_index(self):
        '''
        get field faiss index by computing the IVFPQ index
        :return:
        '''

        if self.produced_field_papers:
            fnames = list(self.produced_field_papers.keys())
        else:
            self.produced_field_papers,_ = self.load_combine_produced_allpapers()
            fnames = list(self.produced_field_papers.keys())

        print('>> Encoding ..')
        to_encode = [self.txt_to_encode(fn) for fn in fnames]
        encoded_fields = self.encoder.encode(to_encode)
        encoded_fields = np.asarray(encoded_fields.astype('float32'))

        print('>> Getting ids ..')
        self.field_index = faiss.IndexIVFPQ(vecs,D,ncentroids,code_size ,8)
        self.field_index.train(encoded_fields)
        self.field_index.add(encoded_fields)

    def update_field_index(self,new_all_papers: str):
        '''
        update existing field index with new all_papers
        :param new_all_papers:
        :return:
        '''
        print(f'Loading new produced papers : {new_all_papers}')
        prod_zone = Production_Zone()
        papers_dict = prod_zone.get_papers(field=self.field, fname=new_all_papers, verbose=True)
        fnames = list(papers_dict.keys())

        print('>> Encoding ..')
        to_encode = [self.txt_to_encode(fn,papers_dict) for fn in fnames]
        encoded_fields = self.encoder.encode(to_encode)
        encoded_fields = np.asarray(encoded_fields.astype('float32'))

        print('>> Adding ids ..')
        if self.field_index.is_trained:
            print('  >> Index is trained !')
            self.field_index.add(encoded_fields)
        else:
            print('  >> Index needs to be retrained ! ')


    def load_field_index(self):
        '''
        Load field faiss index if it exists
        :return:
        '''
        if not self.field_index:
          path = os.path.join(path_produced,self.field,'encodings.index')
          self.field_index = faiss.read_index(path)

    def load_combine_produced_allpapers(self, size_data=0):
        '''
        load & combine production papers in same dictionary. If size_data, take percentage of each all_papers db.
        (same code as in Dispatched_Zone, get_field in naimai.pipelines.zones)
        :return:
        '''
        print('>> Loading production papers')
        path_produced_papers = os.path.join(path_produced, self.field)
        all_files = os.listdir(path_produced_papers)
        paths = [os.path.join(path_produced_papers,fl) for fl in all_files]
        paths = [elt for elt in paths if os.path.isfile(elt) and 'encoding' not in elt and 'sqlite' not in elt] # keep only files

        size_each_all_papers = 0
        if size_data:
            size_each_all_papers = int(size_data/len(paths))+1
            print('>> Each all_papers size : ', size_each_all_papers)

        all_paps = {}
        eval_all_paps= {}
        for p in paths:
            data = load_gzip(p)
            if size_each_all_papers:
                keys = list(data.keys())
                if len(data)>size_each_all_papers:
                    keys_selected= random.sample(keys,size_each_all_papers)
                else:
                    keys_selected = keys
                data = {key: data[key] for key in keys_selected}

            all_paps.update(data)
            # eval_all_paps.update(eval_data)
        return all_paps,eval_all_paps

    def fine_tune_field_encoder(self, size_data: int,save_model: bool,batch_size=16,n_epochs=10):
        '''
        load & combine all the "all papers" & finetune search model using a size 'size_data' from field_papers
        :param size_data:
        :param save_model:
        :param batch_size:
        :param n_epochs:
        :return:
        '''
        # combined_papers = self.load_combine_dispatched_allpapers(size_data)
        combined_papers,combined_eval_papers = self.load_combine_produced_allpapers(size_data=size_data)
        print('Len everything : ', len(combined_papers))
        self.smodel = Search_Model(field=self.field, papers=combined_papers,eval_papers=combined_eval_papers,
                                   batch_size=batch_size, n_epochs=n_epochs)
        if self.encoder:
            self.smodel.model = self.encoder
        self.smodel.fine_tune()
        self.encoder = self.smodel.model
        if save_model:
          self.save_model()

    def save_model(self):
        '''
        Saving the encoder model (when trained on the field papers)
        :return:
        '''
        path = os.path.join(path_produced, self.field, 'search_model')
        self.encoder.save(path)

    def produce_field_papers(self):
        '''
        Produce papers contained in field (dispatched files).
        :return:
        '''
        print('>> Producing field papers..')
        for fname in tqdm(self.dispatched_field_papers):
            pap = self.dispatched_field_papers[fname]
            if pap['Abstract']:
                try:
                    self.produce_paper(paper=pap, paper_name=fname)
                except:
                    pass
        print(' ')

    # def produce(self,save_papers=False,save_field_index=False):
    #     '''
    #     Produce field papers > getting field faiss index.
    #     :param save_papers:
    #     :param save_field_index:
    #     :return:
    #     '''
    #     if self.encoder:
    #         # produce field papers
    #         self.produce_field_papers()
    #
    #         #compute Faiss index
    #         self.get_field_index()
    #
    #         #save
    #         if save_papers:
    #             print('>> Saving papers..')
    #             self.save_papers()
    #
    #         if save_field_index:
    #             print('>> Saving field index..')
    #             self.save_field_index()
    #         print(' ')
    #         print('>> Done!')
    #     else:
    #         print('>> The production is not done (no field encoder). You need to fine tune.')

    def save_field_index(self):
        '''
        save field faiss index for semantic search
        :return:
        '''
        path = os.path.join(path_produced, self.field, 'encodings.index')
        faiss.write_index(self.field_index, path)

    def save_papers(self):
        '''
        save produced papers
        :return:
        '''
        if self.extracted:
            file_name = f'{self.all_papers}_{self.idx_start}_{self.idx_finish}'
        else:
            file_name = self.all_papers
        path = os.path.join(path_produced, self.field, file_name)
        save_gzip(path, self.produced_field_papers)


class Custom_Producer:
    '''
    1 Takes formatted custom papers in dictionary all_papers and transform them into a produced all_paper using Paper Producer obj
    2 no need of field index
    '''
    def __init__(self, all_papers):
        self.obj_classifier = None
        self.bomr_classifier = None
        self.nlp = None
        self.smodel = None
        self.papers_ref_fields = {} # fields used to check if same paper is already produced

        self.all_papers = all_papers

        self.produced_custom_papers = {}
        self.produce_only_fnames=False

        self.load_obj_classifier()
        self.load_bomr_classifier()
        self.load_nlp()

    def load_obj_classifier(self):
        '''
        Load the objective classifier: model that selects the objective sentence in the abstract.
        :param obj_classifier:
        :return:
        '''
        print('>> Loading obj classifier..')
        self.obj_classifier = Objective_classifier()

    def load_bomr_classifier(self):
        '''
        Load the bomr classifier, the model that structures the abstract into bibliography, objectives, methods
        and results.
        :param bomr_classifier:
        :return:
        '''
        print('>> Loading bomr classifier..')
        self.bomr_classifier = NER_BOMR_classifier(load_model=True, path_model=path_bomr_classifier,
                                                       predict_mode=True)
    def load_nlp(self):
        '''
        Load nlp model (spaCy)
        :param nlp:
        :return:
        '''
        print('>> Loading nlp..')
        self.nlp = spacy.load(nlp_vocab)

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
          self.produced_custom_papers[paper_name+'_objectives'] = prod['objectives']
          self.produced_custom_papers[paper_name+'_methods'] = prod['methods']
          self.produced_custom_papers[paper_name+'_results'] = prod['results']

    def txt_to_encode(self,fname: str,papers_dict=None)-> str:
      '''
      get what text to encode from papers_dict (element of self.produced_custom_papers)
      :param fname:
      :return:
      '''
      if not papers_dict:
          papers_dict = self.produced_custom_papers

      messages = ' '.join(papers_dict[fname]['messages'])
      if '_objectives' in fname:
        return papers_dict[fname]['title']+ ' ' + messages
      else:
        return messages

    def produce_custom_papers(self):
        '''
        produce read papers.
        :return:
        '''
        print('>> Producing custom papers..')
        for fname in tqdm(self.all_papers):
            pap = self.all_papers[fname]
            if pap['Abstract']:
                # try:
                self.produce_paper(paper=pap, paper_name=fname)
                # except:
                #     pass
        print(' ')