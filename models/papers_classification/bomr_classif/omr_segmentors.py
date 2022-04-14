from naimai.constants.regex import regex_filtered_words_obj
from naimai.constants.nlp import nlp_vocab
from naimai.constants.paths import path_objective_classifier
from naimai.utils.regex import get_first_last_token_ids
from naimai.models.papers_classification.bomr_classif.ner_processor import NER_BOMR_processor
from naimai.models.papers_classification.bomr_classif.ner_classifier import NER_BOMR_classifier
from naimai.models.papers_classification.obj_classifier import Objective_classifier
import re
import spacy


class OMR_Text_Segmentor:
    '''
    Segment a text to Objective, Method and Results
    '''
    def __init__(self, text, bomr_classifier=None, objective_classifier=None, path_model='',nlp=None,summarize=False):
        self.text = text
        self.ner_processor = None
        if bomr_classifier:
            self.bomr_classifier = bomr_classifier
        elif path_model:
            self.bomr_classifier = NER_BOMR_classifier(load_model=True, path_model=path_model, predict_mode=True)
        print('Predicting & getting ner processor..')
        self.get_ner_processor()
        if objective_classifier:
          self.objective_classifier = objective_classifier
        else:
          print('Getting objectif classifier..')
          self.objective_classifier = Objective_classifier(dir=path_objective_classifier)
        if nlp:
            self.nlp = nlp
        else:
            self.nlp = spacy.load(nlp_vocab)
        doc = self.nlp(text)
        self.sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.split())>4]
        if summarize:
            self.summarize()

        print('Done!')
    def text2bomr(self, text, visualize_=False):
        return self.bomr_classifier.predict(text=text, visualize_=visualize_, dict_format=False)

    def get_ner_processor(self):
        df = self.text2bomr(self.text)
        self.ner_processor = NER_BOMR_processor(text=self.text, df=df)

    def get_sentence_label(self, sentence, last_token=0):
        sentence_range_wids = get_first_last_token_ids(sentence, self.text, last_token)
        range_wids_labels = self.ner_processor.get_range_wids_labels()
        sentence_class = self.ner_processor.get_label_with_most_overlap(sentence_range_wids=sentence_range_wids,
                                                                        range_wids_labels=range_wids_labels)
        return (sentence_class, sentence_range_wids[-1] + 1)

    def segment_naive(self) -> dict:
        '''
        segment text into bomr using longformer/bigbird predictions & ner processor
        :return:
        '''
        last_tokenId = 0
        segmented_text = {}

        for idx, sentence in enumerate(self.sentences):
            segmented_text[idx], last_tokenId = self.get_sentence_label(sentence, last_token=last_tokenId)
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

    def get_objective_sentences(self,sentences):
        objectives = self.objective_classifier.predict(sentences)
        objectives_with_classifier = [obj for obj in objectives if
                                      not re.findall(regex_filtered_words_obj, obj, flags=re.I)]
        return objectives_with_classifier

    def segment(self) -> dict:
        '''
        segment naively the text & process each background classes : get matched objective sentences with objective classifier.
        :return:
        '''
        segmented_text = self.segment_naive()
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

