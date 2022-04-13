import re
import spacy
from naimai.constants.regex import regex_eft, regex_abbrvs,regex_abbrvs2, regex_some_brackets, regex_numbers_in_brackets
from naimai.constants.nlp import nlp_vocab

print('nlp loaded for TextCleaner')
loaded_nlp = spacy.load(nlp_vocab)

class TextCleaner:
    def __init__(self, text,nlp=None):
        self.text = text
        self.cleaned_text = ''
        if nlp:
            self.nlp = nlp
        else:
            print('Loading nlp for TextCleaner..')
            self.nlp = loaded_nlp

    def replace_abbrevs(self,text):
        '''
        replace i.e. and e.g. by meaning in the text, and cf. by "see"
        :param text:
        :return:
        '''
        text1= re.sub(regex_abbrvs,'meaning', text)
        return re.sub(regex_abbrvs2,'see', text1)

    def remove_some_brackets(self,text):
        '''
        remove brackets & square brackets with words figure, table, meaning (that would have replaced i.e. and
        e.g. using replace_abbrevs)
        :param text:
        :return:
        '''
        return re.sub(regex_some_brackets,'',text, flags=re.I)


    def remove_sentence_with_nbs_brackets(self,text):
        '''
        remove sentences that contains number in between brackets & square brackets
        :param text:
        :return:
        '''
        return re.sub(regex_numbers_in_brackets, '', text)

    def remove_sentence_with_eft(self,text):
        '''
        remove sentences that contains the eft terms : equation, figure or table!
        :param text:
        :return:
        '''
        doc = self.nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents]
        sentences_filtered = [stc for stc in sentences if not re.findall(regex_eft,stc,flags=re.I)]
        cleaned_text = '. '.join(sentences_filtered)
        return cleaned_text

    def fix_spaces(self,text):
        '''
        keep only one space between words
        :param text:
        :return:
        '''
        return re.sub('\s+',' ', text)

    def clean(self):
        '''
        clean the text by :
            1. replacing i.e. & e.g. abbreviations by "meaning"
            2. removing brackets with table, figure
            3. removing sentences with [x] or (x), x being a digit
            4. removing sentences with equations, figure or table terms
            5. fixing additional spaces resulted by cleaning methods
        :return:
        '''
        self.text = self.replace_abbrevs(self.text)
        self.text = self.remove_some_brackets(self.text)
        self.text = self.remove_sentence_with_nbs_brackets(self.text)
        self.text = self.remove_sentence_with_eft(self.text)
        self.cleaned_text = self.fix_spaces(self.text)



# class SentenceToProcess:
#     def __init__(self,sentence,nlp=None):
#         if nlp:
#             self.nlp = nlp
#         else:
#             self.nlp = spacy.load(Path(path_nlp))
#         self.sentence = self.nlp(sentence, disable=nlp_disabled_processing)
#
#     def get_NE(self):
#         return self.sentence.ents
#
#     def is_PERSON(self):
#         self.keep_words_commas()
#         self.capitalize_each_word()
#         NEs = self.get_NE()
#
#         if NEs:
#             ln = len(NEs)
#             idx = 0
#
#             for ent in NEs:
#                 if ent.label_ == 'PERSON':
#                   idx += 1
#             if idx >= ln/2:
#                 return True
#             # return False
#         return False
#
#     def remove_NE(self):
#         print('REMOVE NE SHOULD BE CORRECTED SHIT')
#         NEs = self.get_NE()
#         NEs_list = [elt.text for elt in NEs]
#         if NEs_list:
#           result= []
#           for token in self.sentence:
#               if not any(token.text in elt for elt in NEs_list):
#                   result.append(token.text)
#
#           # if len(result) > 2:
#           self.sentence = self.nlp(' '.join(result), disable=nlp_disabled_processing)
#
#
#     def remove_stop_words(self):
#         result= []
#         for token in self.sentence:
#             if not token.is_stop:
#                 result.append(token.text)
#         # if len(result)>2:
#         self.sentence = self.nlp(' '.join(result), disable=nlp_disabled_processing)
#
#     def to_lemma(self):
#         result = []
#         for token in self.sentence:
#             if len(token.lemma_) > 2:
#                 result.append(token.lemma_.lower())
#         # if len(result) > 2:
#         self.sentence = self.nlp(' '.join(result), disable=nlp_disabled_processing)
#
#     def remove_tag(self,tag='VB'):
#         result = []
#         for token in self.sentence:
#             if tag not in token.tag_:
#                 result.append(token.text)
#         # if len(result) > 2:
#         self.sentence = self.nlp(' '.join(result))
#
#     def keep_words(self):
#         sentence=re.sub(regex_words, ' ', self.sentence.text)
#         self.sentence = self.nlp(sentence, disable=nlp_disabled_processing)
#
#         # result = []
#         # for token in self.sentence:
#         #     if token.text.isalpha():
#         #         result.append(token.text)
#         # if len(result) > 2:
#         #     self.sentence = self.nlp(' '.join(result))
#
#     def tokenize(self):
#         result = []
#         for token in self.sentence:
#             if len(token.text)>3:
#                 result.append(token.text)
#         return result
#
#     def keep_words_commas(self):
#         pat = re.compile(regex_words_commas)
#         new_stc = re.sub(pat, '', self.sentence.text)
#         self.sentence= self.nlp(new_stc, disable=nlp_disabled_processing)
#
#     def capitalize_each_word(self):
#         new_stc=capitalize(self.sentence.text)
#         self.sentence= self.nlp(new_stc, disable=nlp_disabled_processing)
#
#     def get_citations(self):
#         NEs = self.get_NE()
#         result=[]
#         for ent in NEs:
#             if ent.label_=='Citation':
#                 citation_verification = verify_citation(ent.text)
#                 if citation_verification:
#                     result.append(ent.text)
#         return result
#
#
#     def clean(self):
#         # self.remove_NE()
#         # self.remove_tag()
#         self.keep_words()
#         self.remove_stop_words()
#         self.to_lemma()
#
#
# class ArticleToProcess:
#     def __init__(self, article,nlp=None):
#         if nlp:
#             self.nlp = nlp
#         else:
#             self.nlp = spacy.load(Path(path_nlp))
#         self.article = article
#         self.sentences = []
#         self.vocab = set()
#         self.tokens = []
#
#     def to_sentences(self):
#         # self.sentences = self.article.split('.')
#         self.sentences = re.split(regex_sentences, self.article)
#
#     def remove_citations(self):
#         txt=self.article
#         stc= SentenceToProcess(txt, self.nlp)
#         citations = stc.get_citations()
#         for elt in citations:
#             txt = txt.replace(elt, '')
#
#         self.article= txt
#
#     def replace_words(self,replacement_dic):
#         self.article = multiple_replace(replacement_dic,self.article)
#
#     def remove_emails(self):
#         emails=re.findall(regex_email, self.article, flags=re.I | re.M)
#
#         emails_replacement = {elt: '' for elt in emails}
#         if emails_replacement:
#             self.article = multiple_replace(emails_replacement,self.article)
#
#     def remove_urls(self):
#         urls=re.findall(regex_url, self.article, flags=re.I | re.M)
#
#         urls_replacement = {elt: '' for elt in urls}
#
#         if urls_replacement:
#             self.article = multiple_replace(urls_replacement,self.article)
#
#
#     def clean(self,replacement_dic=replacement_words,remove_citation=True,replace_words=True, remove_emails=True, remove_urls=True):
#         # remove citations
#         if remove_citation:
#             self.remove_citations()
#
#         if remove_emails:
#             self.remove_emails()
#
#         if remove_urls:
#             self.remove_urls()
#
#         if replace_words:
#             self.replace_words(replacement_dic)
#
#         self.to_sentences()
#         if self.sentences:
#             sentence_tokens=[]
#             for sentence in self.sentences:
#                 if sentence:
#                     sentenceObj = SentenceToProcess(sentence, self.nlp)
#                     sentenceObj.clean()
#                     tokens = sentenceObj.tokenize()
#                     if tokens:
#                         sentence_tokens.append(tokens)
#             self.tokens = [elt for elt2 in sentence_tokens for elt in elt2 if ' ' not in elt]
#             self.vocab = set(self.tokens)
#
#




