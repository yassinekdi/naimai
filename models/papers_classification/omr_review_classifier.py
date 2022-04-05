from naimai.papers.full_text.pmc import paper_pmc
import re
from naimai.constants.regex import regex_abstract_omr
from naimai.models.papers_classification.obj_classifier import Objective_classifier
from naimai.constants.paths import path_objective_classifier
from naimai.constants.regex import regex_filtered_words_obj, regex_objectives, regex_review

class Omr_Review_Paper_Classifier:
    def __init__(self,paper: paper_pmc,objective_classifier=None):
        if objective_classifier:
            self.objective_classifier = objective_classifier
        else:
            print('Need GPU to faster things..')
            self.objective_classifier = Objective_classifier(dir=path_objective_classifier)
        self.paper = paper

    def get_paper_abstract(self ) -> str:
        '''
        get abstract paper
        :param paper:
        :return:
        '''
        abstract =self.paper.get_Abstract(stacked=False)
        return abstract

    def get_paper_title(self) -> str:
        '''
        get title of paper
        :param paper:
        :return:
        '''
        self.paper.get_Title()
        return self.paper.Title

    def get_paper_text(self) -> str:
        '''
        stack title & abstract in same text
        :param paper:
        :return:
        '''
        title = self.get_paper_title()
        abstract = self.get_paper_abstract()
        text = title + ' ' + abstract
        return text

    def is_text_omr(self ,text) -> bool:
        '''
        detect if the text has omr sections or no based on regex_abstract_omr
        :param text:
        :return:
        '''
        if re.findall(regex_abstract_omr ,text ,re.I):
            return True
        return False

    def find_obj(self,text)->str:
        '''
        identify obj using regex & obj classifier and stack them
        :param text:
        :return:
        '''
        obj_rgx = list(set(re.findall(regex_objectives, text, flags=re.I)))

        list_sentences = text.split('.')
        objs_clf = self.objective_classifier.predict(list_sentences)
        objs_clf = [obj for obj in objs_clf if
                                      not re.findall(regex_filtered_words_obj, obj, flags=re.I)]

        objectives = obj_rgx + objs_clf
        objectives = list(set(objectives))
        if objectives:
            return ' '.join(objectives)
        return ''
    def is_objective_review(self,objective: str) -> bool:
        '''
        objective is considered as review & return True if it contains regex_review. Otherwise it's False (then OMR)
        :param objective:
        :return:
        '''
        if objective:
            if re.findall(regex_review,objective,re.I):
                return True
        return False

    def is_paper_review(self) -> bool:
        '''
        identify is paper is review or not by :
            1. checking if it has omr format, in which case it's not a review paper
            2. check if its obj sentences contains some review terms, in which case it's considered a review paper
        :param paper:
        :return:
        '''
        text = self.get_paper_text()

        if self.is_text_omr(text):
            return False

        objectives = self.find_obj(text)
        is_obj_review = self.is_objective_review(objectives)
        return is_obj_review

