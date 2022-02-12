from .direct2reported import Direct2Reported
from .clauses_processing import objective_sentence_processor
from naimai.constants.nlp import nlp_vocab
from naimai.utils import authors_with_commas, authors_with_period, authors_with_full_name
import spacy


class Paper2Reported:
    def __init__(self, paper, paper_objectives, nlp=None):
        self.paper = paper
        self.paper_objectives = paper_objectives
        self.paper_year = 999
        self.paper_authors = ''
        self.reported = []
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
        return result

    # def choose_objective(self):
    #     len_objs = len(self.paper_objectives)
    #     idx_obj = 0
    #     if len_objs > 1:
    #         len_obj_elts = [len(el.split()) for el in self.paper_objectives]
    #         if self.complexity:  # long objectives
    #             idx_obj = len_obj_elts.index(max(len_obj_elts))
    #         else:
    #             idx_obj = len_obj_elts.index(min(len_obj_elts))
    #     chosen = self.paper_objectives[idx_obj]
    #     self.objective_queue = [obj for obj in self.paper_objectives if obj != chosen]
    #     return chosen

    # def gather_authors_objectives(self):
    #     if self.paper_objectives:
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
        authors = self.process_authors()


        for obj in self.paper_objectives:
            try :
                obj_processor = objective_sentence_processor(sentence=obj, nlp=self.nlp)
                obj_processor.process()
                obj_transformed = obj_processor.final_sentence
            except:
                obj_transformed = obj
            try:
                writer = Direct2Reported(authors=authors, sentence=obj_transformed, nlp=self.nlp)
                writer.generate()
                if writer.reported:
                    self.reported.append(writer.reported)
                else:
                    writer = Direct2Reported(authors=authors, sentence=obj, nlp=self.nlp)
                    writer.generate()
                    self.reported.append(writer.reported)
            except:
                with open('objectives_pbs.txt', 'a') as f:
                    f.write('problem with objective : {} // doi : {} - dbase : {} \n\n'.format(obj,self.paper['doi'],self.paper['database']))




        # collect = self.gather_authors_objectives()
        # if collect:
        #     authors, paper_obj = collect
        #     try:
        #         writer = Direct2Reported(authors=authors, sentence=paper_obj, nlp=self.nlp)
        #         writer.generate()
        #     except:
        #         reported = False
        #         while self.objective_queue and not reported:
        #             new_obj = self.change_objective()
        #             writer = Direct2Reported(authors=authors, sentence=new_obj, nlp=self.nlp)
        #             try:
        #                 writer.generate()
        #                 reported = True
        #             except:
        #                 reported = False
        #     if writer:
        #         self.reported = writer.reported