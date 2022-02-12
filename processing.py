import re
import spacy
from pathlib import Path

from .constants.regex import regex_email, regex_url, regex_words, regex_words_commas, regex_sentences
from .constants.nlp import nlp_disabled_processing
from .constants.replacements import replacement_words
from .constants.paths import path_nlp
from .utils import multiple_replace, verify_citation, capitalize

class SentenceToProcess:
    def __init__(self,sentence,nlp=None):
        if nlp:
            self.nlp = nlp
        else:
            self.nlp = spacy.load(Path(path_nlp))
        self.sentence = self.nlp(sentence, disable=nlp_disabled_processing)

    def get_NE(self):
        return self.sentence.ents

    def is_PERSON(self):
        self.keep_words_commas()
        self.capitalize_each_word()
        NEs = self.get_NE()

        if NEs:
            ln = len(NEs)
            idx = 0

            for ent in NEs:
                if ent.label_ == 'PERSON':
                  idx += 1
            if idx >= ln/2:
                return True
            # return False
        return False

    def remove_NE(self):
        print('REMOVE NE SHOULD BE CORRECTED SHIT')
        NEs = self.get_NE()
        NEs_list = [elt.text for elt in NEs]
        if NEs_list:
          result= []
          for token in self.sentence:
              if not any(token.text in elt for elt in NEs_list):
                  result.append(token.text)

          # if len(result) > 2:
          self.sentence = self.nlp(' '.join(result), disable=nlp_disabled_processing)


    def remove_stop_words(self):
        result= []
        for token in self.sentence:
            if not token.is_stop:
                result.append(token.text)
        # if len(result)>2:
        self.sentence = self.nlp(' '.join(result), disable=nlp_disabled_processing)

    def to_lemma(self):
        result = []
        for token in self.sentence:
            if len(token.lemma_) > 2:
                result.append(token.lemma_.lower())
        # if len(result) > 2:
        self.sentence = self.nlp(' '.join(result), disable=nlp_disabled_processing)

    def remove_tag(self,tag='VB'):
        result = []
        for token in self.sentence:
            if tag not in token.tag_:
                result.append(token.text)
        # if len(result) > 2:
        self.sentence = self.nlp(' '.join(result))

    def keep_words(self):
        sentence=re.sub(regex_words, ' ', self.sentence.text)
        self.sentence = self.nlp(sentence, disable=nlp_disabled_processing)

        # result = []
        # for token in self.sentence:
        #     if token.text.isalpha():
        #         result.append(token.text)
        # if len(result) > 2:
        #     self.sentence = self.nlp(' '.join(result))

    def tokenize(self):
        result = []
        for token in self.sentence:
            if len(token.text)>3:
                result.append(token.text)
        return result

    def keep_words_commas(self):
        pat = re.compile(regex_words_commas)
        new_stc = re.sub(pat, '', self.sentence.text)
        self.sentence= self.nlp(new_stc, disable=nlp_disabled_processing)

    def capitalize_each_word(self):
        new_stc=capitalize(self.sentence.text)
        self.sentence= self.nlp(new_stc, disable=nlp_disabled_processing)

    def get_citations(self):
        NEs = self.get_NE()
        result=[]
        for ent in NEs:
            if ent.label_=='Citation':
                citation_verification = verify_citation(ent.text)
                if citation_verification:
                    result.append(ent.text)
        return result


    def clean(self):
        # self.remove_NE()
        # self.remove_tag()
        self.keep_words()
        self.remove_stop_words()
        self.to_lemma()


class ArticleToProcess:
    def __init__(self, article,nlp=None):
        if nlp:
            self.nlp = nlp
        else:
            self.nlp = spacy.load(Path(path_nlp))
        self.article = article
        self.sentences = []
        self.vocab = set()
        self.tokens = []

    def to_sentences(self):
        # self.sentences = self.article.split('.')
        self.sentences = re.split(regex_sentences, self.article)

    def remove_citations(self):
        txt=self.article
        stc= SentenceToProcess(txt, self.nlp)
        citations = stc.get_citations()
        for elt in citations:
            txt = txt.replace(elt, '')

        self.article= txt

    def replace_words(self,replacement_dic):
        self.article = multiple_replace(replacement_dic,self.article)

    def remove_emails(self):
        emails=re.findall(regex_email, self.article, flags=re.I | re.M)

        emails_replacement = {elt: '' for elt in emails}
        if emails_replacement:
            self.article = multiple_replace(emails_replacement,self.article)

    def remove_urls(self):
        urls=re.findall(regex_url, self.article, flags=re.I | re.M)

        urls_replacement = {elt: '' for elt in urls}

        if urls_replacement:
            self.article = multiple_replace(urls_replacement,self.article)


    def clean(self,replacement_dic=replacement_words,remove_citation=True,replace_words=True, remove_emails=True, remove_urls=True):
        # remove citations
        if remove_citation:
            self.remove_citations()

        if remove_emails:
            self.remove_emails()

        if remove_urls:
            self.remove_urls()

        if replace_words:
            self.replace_words(replacement_dic)

        self.to_sentences()
        if self.sentences:
            sentence_tokens=[]
            for sentence in self.sentences:
                if sentence:
                    sentenceObj = SentenceToProcess(sentence, self.nlp)
                    sentenceObj.clean()
                    tokens = sentenceObj.tokenize()
                    if tokens:
                        sentence_tokens.append(tokens)
            self.tokens = [elt for elt2 in sentence_tokens for elt in elt2 if ' ' not in elt]
            self.vocab = set(self.tokens)






