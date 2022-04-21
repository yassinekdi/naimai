from naimai.constants.regex import regex_filtered_words_obj
from naimai.constants.nlp import nlp_vocab
from naimai.constants.paths import path_bomr_classifier
from naimai.utils.regex import get_first_last_token_ids
from naimai.models.papers_classification.bomr_classif.ner_processor import NER_BOMR_processor
from naimai.models.papers_classification.bomr_classif.ner_classifier import NER_BOMR_classifier
from naimai.models.papers_classification.obj_classifier import Objective_classifier
import re
import spacy


def segment(text, obj_clf=None, bomr_clf=None, path_bomr_clf=path_bomr_classifier, summarize=True, check_bg=False, visualize_=True):
    '''
    segment a text using OMR_Text_Segmentor.
    :param text:
    :param obj_clf:
    :param bomr_clf:
    :param summarize:
    :param check_bg:
    :param visualize_:
    :param filter_bg:
    :return:
    '''
    segmentor = OMR_Text_Segmentor(text=text, objective_classifier=obj_clf,
                                   bomr_classifier=bomr_clf, summarize=summarize,path_bomr_clf=path_bomr_clf)
    if visualize_:
        segmentor.bomr_classifier.predict(text=segmentor.text, visualize_=True, dict_format=False)

    segmented = segmentor.segment(check_bg=check_bg)
    background_in = 'background' in segmented.values()
    if background_in:
        stcs = [segmentor.sentences[idx] for idx in segmented if segmented[idx] != 'background']
        summarized = ' '.join(stcs)
        segmentor = OMR_Text_Segmentor(text=summarized, objective_classifier=segmentor.objective_classifier,
                                      bomr_classifier=segmentor.bomr_classifier, summarize=False)
        if visualize_:
            print('')
            print('visualization of summarized : ')
            segmentor.bomr_classifier.predict(text=segmentor.text, visualize_=True, dict_format=False)

        segmented = segmentor.segment(check_bg=False)
    return (segmented,segmentor.sentences,segmentor.objective_classifier,segmentor.bomr_classifier)

class OMR_Text_Segmentor:
    '''
    Segment a text to Objective, Method and Results
    '''
    def __init__(self, text, bomr_classifier=None, objective_classifier=None, path_bomr_clf=path_bomr_classifier,nlp=None,summarize=False):
        self.text = text
        self.ner_processor = None
        # self.range_wids_labels=None

        # Segment to sentences
        if not nlp:
            nlp = spacy.load(nlp_vocab)
        doc = nlp(text)
        regex_online_version = 'online version'
        self.sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.split())>5 and not re.findall(regex_online_version,sent.text,flags=re.I)]
        self.text = ' '.join(self.sentences)

        # Get obj classifier
        self.objective_classifier = None
        self.load_obj_classifier(objective_classifier)

        if summarize:
            self.summarize()

        # Get bomr classifier
        self.bomr_classifier=None
        self.load_bomr_classifier(bomr_classifier,path=path_bomr_clf)

    def load_obj_classifier(self, obj_classifier):
        if obj_classifier:
            self.objective_classifier = obj_classifier
        else:
            print('>> Loading obj classifier..')
            self.objective_classifier = Objective_classifier()

    def load_bomr_classifier(self, bomr_classifier,path=path_bomr_classifier):
        if bomr_classifier:
            self.bomr_classifier = bomr_classifier
        else:
            print('>> Loading bomr classifier..')
            self.bomr_classifier = NER_BOMR_classifier(load_model=True, path_model=path,
                                                       predict_mode=True, verbose=False)

    def text2bomr(self, text, visualize_=False):
        return self.bomr_classifier.predict(text=text, visualize_=visualize_, dict_format=False)

    def get_ner_processor(self,text):
        df = self.text2bomr(text)
        return NER_BOMR_processor(text=self.text, df=df)

    def get_sentence_label(self, sentence, ner_processor,range_wids_labels,last_token=0):
        sentence_range_wids = get_first_last_token_ids(sentence, self.text, last_token)
        # if not self.range_wids_labels:

        sentence_class = ner_processor.get_label_with_most_overlap(sentence_range_wids=sentence_range_wids,
                                                                        range_wids_labels=range_wids_labels)
        return (sentence_class, sentence_range_wids[-1] + 1)

    def segment_naive(self) -> dict:
        '''
        segment text into bomr using longformer/bigbird predictions & ner processor
        :return:
        '''
        last_tokenId = 0
        segmented_text = {}
        ner_processor = self.get_ner_processor(self.text)
        range_wids_labels = ner_processor.get_range_wids_labels()
        for idx, sentence in enumerate(self.sentences):
            segmented_text[idx], last_tokenId = self.get_sentence_label(sentence=sentence,
                                                                        ner_processor=ner_processor,
                                                                        range_wids_labels=range_wids_labels,
                                                                        last_token=last_tokenId)
        return segmented_text

    def summarize(self):
        '''
        filter sentences using objective classifier
        :return:
        '''
        sentences= self.get_objective_sentences(self.sentences)
        if len(sentences)>3:
            self.sentences=sentences
            self.text = ' '.join(self.sentences)

    def get_objective_sentences(self,sentences: list):
        objectives = self.objective_classifier.predict(sentences)
        objectives_with_classifier = [obj for obj in objectives if
                                      not re.findall(regex_filtered_words_obj, obj, flags=re.I)]
        return objectives_with_classifier

    def filter_background(self,segmented_text: dict)-> dict:
        '''
         process each background classes : get matched objective sentences with objective classifier.
        :param segmented_text:
        :return:
        '''
        regex_bground = 'background'
        bground_sentences = [self.sentences[idx] for idx in segmented_text if
                             re.findall(regex_bground, segmented_text[idx])]

        objectives_with_classifier = self.get_objective_sentences(bground_sentences)
        obj_sentences_ids = [self.sentences.index(elt) for elt in objectives_with_classifier]

        corrected = {}
        for idx in obj_sentences_ids:
            corrected[idx] = 'objectives'

        for idx in segmented_text:
            if not re.findall(regex_bground, segmented_text[idx]):
                corrected[idx] = segmented_text[idx]
        return corrected

    def segment(self,check_bg=False) -> dict:
        '''
        segment naively the text & if check_bg, extract objectives from bground using filter_background.
        if remove_bg_resegment, remove background from segmentation and recompute.
        :param check_background:
        :return:
        '''
        segmented_text = self.segment_naive()
        if check_bg:
            segmented_text = self.filter_background(segmented_text)
        #
        # if remove_bg_resegment:
        #     segmented_text = self.segment_without_bground(segmented_text)

        return segmented_text

