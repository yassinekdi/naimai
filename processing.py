import re
import spacy
from naimai.constants.regex import regex_eft, regex_abbrvs,regex_abbrvs2, regex_some_brackets,\
    regex_numbers_in_brackets, regex_equation, regex_etal, regex_equation_tochange, regex_explained_2pts
from naimai.utils.regex import remove_between_brackets
from naimai.constants.nlp import nlp_vocab

print('nlp loaded for TextCleaner')
print('')
loaded_nlp = spacy.load(nlp_vocab)

class TextCleaner:
    def __init__(self, text,nlp=None):
        self.text = text
        self.cleaned_text = ''
        if nlp:
            self.nlp = nlp
        else:
            self.nlp = loaded_nlp

    def remove_explanations(self,text):
        '''
        remove text after ':' that explains stuff.
        :param text:
        :return:
        '''
        return re.sub(regex_explained_2pts,'.',text)
    def replace_abbrevs(self,text):
        '''
        replace i.e. and e.g. by meaning in the text & cf. by "see" & et al. by et al
        :param text:
        :return:
        '''
        text1= re.sub(regex_abbrvs,'meaning', text)
        text2 = re.sub(regex_etal,'et al', text1)
        return re.sub(regex_abbrvs2,'see', text2)

    def remove_some_brackets(self,text):
        '''
        remove brackets with > 5 words & brackets and square brackets with words figure, table, meaning (that would have replaced i.e. and
        e.g. using replace_abbrevs)
        :param text:
        :return:
        '''
        txt2 = remove_between_brackets(text)
        return re.sub(regex_some_brackets,'',txt2, flags=re.I)


    def remove_sentence_with_nbs_brackets(self,text):
        '''
        remove sentences that contains number in between brackets & square brackets
        :param text:
        :return:
        '''
        return re.sub(regex_numbers_in_brackets, '', text)

    def remove_sentence_with_eft(self,text):
        '''
        remove sentences that contains equations & the eft terms : equation, figure or table!
        :param text:
        :return:
        '''
        text_stacked_eqs = re.sub(regex_equation_tochange,r'\1=\2',text)
        doc = self.nlp(text_stacked_eqs)
        sentences = [sent.text.strip() for sent in doc.sents]
        sentences_filtered1 = [stc for stc in sentences if not re.findall(regex_equation, stc, flags=re.I)] # remove sentences with eqs
        sentences_filtered2 = [stc for stc in sentences_filtered1 if not re.findall(regex_eft,stc,flags=re.I)] # remove sentences with eft
        sentences_filtered3 = [stc for stc in sentences_filtered2 if len(stc.split())>3]
        cleaned_text = '. '.join(sentences_filtered3)
        return cleaned_text

    def fix_spaces(self,text):
        '''
        keep only one space between words & replace 2 points in row
        :param text:
        :return:
        '''
        txt2 = re.sub('\.\s*\.','.',text)
        return re.sub('\s+',' ', txt2)

    def clean(self):
        '''
        clean the text by :
            1. remove explained text that happens after ':'
            2. replacing i.e. & e.g. abbreviations by "meaning"
            3. removing brackets with table, figure
            4. removing sentences with [x] or (x), x being a digit
            5. removing sentences with equations, figure or table terms
            6. fixing additional spaces & other stuff resulted by cleaning methods
        :return:
        '''
        self.text = self.remove_explanations(self.text)
        self.text = self.replace_abbrevs(self.text)
        self.text = self.remove_some_brackets(self.text)
        self.text = self.remove_sentence_with_nbs_brackets(self.text)
        self.text = self.remove_sentence_with_eft(self.text)
        self.cleaned_text = self.fix_spaces(self.text)



