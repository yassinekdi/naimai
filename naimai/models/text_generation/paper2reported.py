from .direct2reported import Direct2Reported
from .clauses_processing import objective_sentence_processor
from naimai.constants.nlp import nlp_vocab
from naimai.utils.regex import authors_with_commas, authors_with_full_name
import spacy
import numpy as np

class Paper2Reported:
    def __init__(self, paper, messages, paper_name='',nlp=None):
        self.paper = paper
        self.paper_name = paper_name
        self.messages = messages
        self.paper_year = 999
        self.paper_authors = ''
        self.processed_authors=''
        self.list_reported = []
        self.reported_objective = ''
        self.objective_queue = []
        if nlp:
            self.nlp = nlp
        else:
            self.nlp = spacy.load(nlp_vocab)

    def get_paper_year(self):
        paper_year = self.paper['year']
        if paper_year != 999:
            self.paper_year = paper_year
        else:
            self.paper_year = ''

    def get_paper_authors(self):
        if self.paper['Authors']:
            self.paper_authors = self.paper['Authors']
        else:
            self.paper_authors = 'Some authors'

    def process_authors(self):
        str_year = ' (' + str(self.paper_year) + ')'
        authors = self.paper_authors
        result = ''
        if len(authors.split()) == 2:
            result = authors.split()[1] + str_year
        else:
            try:
                if ',' in authors:
                    result = authors_with_commas(authors) + str_year
                else:
                    authors_formula = authors_with_full_name(authors)
                    if authors_formula:
                        if "." in authors_formula:
                            result = authors_formula + str_year
                        else:
                            result = authors_with_full_name(authors) + str_year
                    else:
                        result = 'Some authors ' + str_year
            except:
                print('problem authors with paper of doi {} - dbase {} '.format(self.paper['doi'],self.paper['database']))
        self.processed_authors= result

    # def choose_objective(self):
    #     len_objs = len(self.messages)
    #     idx_obj = 0
    #     if len_objs > 1:
    #         len_obj_elts = [len(el.split()) for el in self.messages]
    #         if self.complexity:  # long objectives
    #             idx_obj = len_obj_elts.index(max(len_obj_elts))
    #         else:
    #             idx_obj = len_obj_elts.index(min(len_obj_elts))
    #     chosen = self.messages[idx_obj]
    #     self.objective_queue = [obj for obj in self.messages if obj != chosen]
    #     return chosen

    # def gather_authors_objectives(self):
    #     if self.messages:
    #         self.get_paper_authors()
    #         authors = self.process_authors()
    #         self.get_paper_year()
    #         paper_obj = self.choose_objective()
    #         return (authors, paper_obj)
    #     return
    #
    # def change_objective(self):
    #     chosen = self.objective_queue[0]
    #     self.objective_queue.remove(chosen)
    #     return chosen

    def generate(self):
        writer = None
        self.get_paper_year()
        self.get_paper_authors()
        self.process_authors()


        for obj in self.messages:
            try :
                obj_processor = objective_sentence_processor(sentence=obj, nlp=self.nlp)
                obj_processor.process()
                obj_transformed = obj_processor.final_sentence
            except:
                obj_transformed = obj
            try:
                writer = Direct2Reported(authors=self.processed_authors, sentence=obj_transformed, nlp=self.nlp)
                writer.generate()
                if writer.reported:
                    self.list_reported.append(writer.reported)
                else:
                    writer = Direct2Reported(authors=self.processed_authors, sentence=obj, nlp=self.nlp)
                    writer.generate()
                    self.list_reported.append(writer.reported)
            except:
                with open('objectives_pbs.txt', 'a') as f:
                    f.write('problem with objective : {} // paper : {} - dbase : {} \n\n'.format(obj,self.paper_name,self.paper['database']))

    def choose_obj_in_mean_lengths_range(self,mean_objs):
        mean_lens = 22
        if len(mean_objs) == 1:
            return mean_objs[0]
        else:
            # take the closest len to the mean 22
            closest_to_mean = min(mean_objs, key=lambda x: abs(len(x.split()) - mean_lens))
            return closest_to_mean

    def choose_obj_beyond_mean_lengths_range(self, references):
        mean_lens_radius = np.arange(20, 26)
        closest_to_min_radius = min(references, key=lambda x: abs(len(x.split()) - mean_lens_radius[0]))
        return closest_to_min_radius

    def choose_objective(self):
        mean_lens_radius = np.arange(20, 26)
        if len(self.list_reported) == 1:  # if only one ref, take it
            self.reported_objective= self.list_reported[0]
        if len(self.list_reported) > 1:  # keep lengths in mean lengths radius 20-25
            mean_objs = [elt for elt in self.list_reported if len(elt.split()) in mean_lens_radius]
            if mean_objs:  # we have objs in the lengths radius:
                self.reported_objective = self.choose_obj_in_mean_lengths_range(mean_objs)
            else:  # so len(references)>1 and lengths of all refs are either < 20 (so we take the one with max length)
                # or > 26 (so we take the one with min length)
                self.reported_objective=  self.choose_obj_beyond_mean_lengths_range(self.list_reported)
