import numpy as np
import pandas as pd
import ast
import re
import random
from tqdm.notebook import tqdm

tqdm.pandas()

from naimai.constants.regex import regex_background, regex_objective,regex_methods,regex_results, regex_objectives
from naimai.papers.full_text.pmc import paper_pmc

def entity_annotate(text, label):
    split = text.split()
    if label=='other':
        entities_labels = ['O' for _ in split]
    else:
        entities_labels = ['B-{}'.format(label)]
        for _ in split[1:]:
            entities_labels.append('I-{}'.format(label))
    return entities_labels

def tostr(lst):
  lst2=[str(elt) for elt in lst]
  return ' '.join(lst2)



class OMRData:
    '''
      Construct data for OMR classification, based on pmc dataframes :
          1. transform structured abstracts to the BOMR structure {Background:.., Objective:.., Methods:.., Results:..}
          2. move objective phrases in background (if exist) to objective section in BOMR
          3. add Other phrases from the body (that would be classified as O in NER labelling), we then get : BOMRO (BOMR + 'Other' section)
          3. convert BOMRO dict to df
          4. Stack & Format the data in the input format for the classifiers
      '''
    def __init__(self, data_df=None,path_data=''):
        if path_data:
            data = pd.read_csv(path_data)
        else:
            data = data_df
        data['is_structured'] = data['abstract'].apply(self.is_structured)
        self.data = data[['doi', 'abstract','body']][data['is_structured'] == True] # only structured abstracts & dois & body are selected
        self.data = self.data.reset_index(drop=True)
        self.transformed_data = None
        self.NER_data = None
        self.BOMRO_class_num = {'ba':0,'ob':1,'me':2,'re':3,'ot':4}

    def is_structured(self,text):
        '''
        check if abstract is structured
        :param text:
        :return:
        '''
        txt2dic = ast.literal_eval(text)
        keys_str = ' '.join(list(txt2dic.keys()))
        if re.findall('text|review|question|meaning|finding',keys_str, flags=re.I):
            return False
        return True

    def is_background(self,text):
        if re.findall(regex_background,text,flags=re.I):
            return True
        return False

    def is_objective(self,text):
        if re.findall(regex_objective,text,flags=re.I):
            return True
        return False

    def is_methods(self,text):
        if re.findall(regex_methods,text,flags=re.I):
            return True
        return False

    def is_results(self,text):
        if re.findall(regex_results,text,flags=re.I):
            return True
        return False

    def abstractKeys2BOMR_format(self,abstract_keys):
        '''
        map abstract keys to BOMR format
        :param abstract_dict:
        :return:
        '''
        BOMR = {'background': [], 'objectives': [], 'methods': [], 'results': []}
        for head in abstract_keys:
            if self.is_background(head):
                BOMR['background'].append(head)
            elif self.is_objective(head):
                BOMR['objectives'].append(head)
            elif self.is_methods(head):
                BOMR['methods'].append(head)
            elif self.is_results(head):
                BOMR['results'].append(head)
        return BOMR

    def correct_BOMR(self, BOMR):
        '''
        objective phrases can often be found in background section. Here we move it to the objective section
        :param BOMR:
        :return:
        '''
        if BOMR['background']:
            obj_phrases = re.findall(regex_objectives,BOMR['background'],flags=re.I)
            if obj_phrases:
                for obj in obj_phrases:
                    BOMR['objectives']+= obj
                    BOMR['background']=BOMR['background'].replace(obj,'')
        BOMR['objectives'] = BOMR['objectives'].replace('\xa0','').strip()
        BOMR['background'] = BOMR['background'].replace('\xa0','').strip()
        BOMR['methods'] = BOMR['methods'].replace('\xa0','').strip()
        BOMR['results'] = BOMR['results'].replace('\xa0','').strip()
        return BOMR

    def abstract2BOMRO(self, abstract_dict):
        '''
        map abstract dict to BOMRO dict
        :param abstract_dict:
        :return:
        '''
        BOMR = {'background': '', 'objectives': '', 'methods': '', 'results': ''}
        if not isinstance(abstract_dict,dict):
            abstract_dict = ast.literal_eval(abstract_dict)
        abstract_keys = list(abstract_dict.keys())
        BOMR_format = self.abstractKeys2BOMR_format(abstract_keys)
        for head in BOMR_format:
            abstract_headers = BOMR_format[head]
            for header in abstract_headers:
                BOMR[head] +=' '.join(abstract_dict[header])
            if self.is_long_sentence(BOMR[head]):
                BOMR[head]=BOMR[head].strip()
            else:
                BOMR[head]=''
        BOMR_corrected = self.correct_BOMR(BOMR) #move obj phrases from background to objective

        idx_df = self.data.index[self.data['abstract']==str(abstract_dict)].to_list()[0]
        other_sentences = self.get_O_entity_label(idx=idx_df)
        if other_sentences:
            BOMR['other'] = [elt.strip() for elt in other_sentences]
            BOMR['other'] = '. '.join(BOMR['other'])
            BOMR['other']=BOMR['other'].strip()
        else:
            BOMR['other']=''

        return BOMR_corrected

    def get_headers_order(self,order='BOMR'):
        '''
        give list of BOMR headers following one of 3 orders :
            1. BOMR
            2. OBMR
            3. MOBR
        the Other section is randomply placed either at the beginning or the end.
        :param order:
        :return: list of headers
        '''
        if order=='BOMR':
            result= ['background', 'objectives', 'methods', 'results']
        elif order=='OBMR':
            result= ['objectives','background','methods','results']
        elif order=='MOBR':
            result= ['methods','objectives','background','results']
        else:
            print('not well written.., returned the default BOMR')
            result= ['background', 'objectives', 'methods', 'results']

        condition=random.choice([0,1])
        if condition:
            result = ['other'] + result
        else:
            result += ['other']
        return result

    def BOMR2dict_data(self,BOMR,id_BOMR,order='BOMR'):
        '''
        transforms BOMR dictionary into data disctionary following the given order. Default order : BOMR. if add_other,
        get other sentences that are not BOMR
        :param BOMR: BOMR dictionary
        :param id_BOMR: id of the BOMR
        :param order: string : BOMR, OBMR or MOBR
        :return:
        '''
        headers= self.get_headers_order(order=order)
        dict_data = {'doi': [], 'text': [], 'start': [], 'end': [], 'predictionstring': [], 'class': [], 'class_num': []}

        id_str_start = 0
        last_word_id = 0
        # id_str_finish = 0
        for head in headers:
            text = BOMR[head]
            if text:
                dict_data['text'].append(text)
                dict_data['start'].append(id_str_start)
                dict_data['end'].append(id_str_start+len(text)-1)
                words_ids = list(np.arange(len(text.split()))+last_word_id+1)
                dict_data['predictionstring'].append(words_ids)
                dict_data['class'].append(head)
                first_class_letter = head[:2]
                dict_data['class_num'].append(self.BOMRO_class_num[first_class_letter])

                id_str_start+=len(BOMR[head])
                last_word_id=words_ids[-1]

        dict_data['doi'] = [id_BOMR]*len(dict_data['text'])

        return dict_data

    def BOMR2text(self,BOMR,order='BOMR'):
        '''
        transforms BOMR dictionary into plain text following the given order. Default order : BOMR (with other at the beginning or end)
        :param BOMR:
        :param order:
        :return:
        '''
        headers = self.get_headers_order(order=order)
        text=''
        for head in headers:
            text +=' ' + BOMR[head]

        return text.strip()

    def BOMR2entities(self,BOMR,order='BOMR'):
        '''
        transforms BOMR dictionary into entities labels : B-label, I-label...
        :param BOMR:
        :return:
        '''
        headers = self.get_headers_order(order=order)
        entities = {}
        for head in headers:
            entities[head] = entity_annotate(text=BOMR[head],label=head)
        return entities

    def data2BOMR_df(self,tqdm=True):
        '''
        convert the data df to BOMR dataframe, with starts, end, etc for each sentence
        :return:
        '''
        if tqdm:
            list_BOMR_dicts = list(self.data['abstract'].progress_apply(self.abstract2BOMRO))
        else:
            list_BOMR_dicts = list(self.data['abstract'].apply(self.abstract2BOMRO))
        list_dois = list(self.data['doi'])
        list_bomr_dfs = []
        for bomr,doi in zip(list_BOMR_dicts,list_dois):
            dict_data = self.BOMR2dict_data(bomr,doi)
            df = pd.DataFrame(dict_data)
            list_bomr_dfs.append(df)
        try:
            dfs_concatenated = pd.concat(list_bomr_dfs, ignore_index=True)
            dfs_concatenated['start']= dfs_concatenated['start'].astype(int)
            dfs_concatenated['end']= dfs_concatenated['end'].astype(int)
            dfs_concatenated['class_num']= dfs_concatenated['class_num'].astype(int)
            dfs_concatenated['predictionstring'] = dfs_concatenated['predictionstring'].apply(tostr)
            self.transformed_data= dfs_concatenated
        except:
            pass

    def data2BOMR_NER_df(self,tqdm=True, weights=(60, 20, 20)):
        '''
        convert the data df to BOMR dataframe only with doi, text and entities. This could be the input to NER model
        :param tqdm: show tqdm
        :param weights: weights of BOMR, OBMR & MOBR
        :return:
        '''
        if tqdm:
            list_BOMR_dicts = list(self.data['abstract'].progress_apply(self.abstract2BOMRO))
        else:
            list_BOMR_dicts = list(self.data['abstract'].apply(self.abstract2BOMRO))
        list_dois = list(self.data['doi'])
        abstract_list = []
        entities_list = []
        order_list=[]
        orders = ['BOMR', 'OBMR', 'MOBR']
        for bomr,doi in zip(list_BOMR_dicts,list_dois):
            order=random.choices(orders, weights=weights, k=1)[0]
            abstract_list.append(self.BOMR2text(bomr,order=order))
            entities=self.BOMR2entities(bomr,order=order)
            entities_vals = []
            for head in entities:
                entities_vals += entities[head]
            entities_list.append(entities_vals)
            order_list.append(order)
        self.NER_data = pd.DataFrame({'doi': list_dois,
                           'text': abstract_list,
                           'entities': entities_list,
                           'order_list': order_list})
    def is_long_sentence(self,sentence: str,threshold=8):
        split = sentence.split()
        if len(split)>threshold:
            return True
        return False


    def get_O_entity_from_text(self,text):
        '''
        get labeled O entities from text
        :param text:
        :return:
        '''
        regex_words_numbers_some = r'[^A-Za-z\s\.,]'
        text_filtered = re.sub(regex_words_numbers_some,'',text)
        text_filtered = re.sub('\s+',' ',text_filtered).strip()
        split = text_filtered.split('.')
        split_filtered = [elt for elt in split if self.is_long_sentence(elt)]
        split_no_obj = [elt for elt in split_filtered if not re.findall(regex_objectives,elt,flags=re.I)]
        if split_no_obj:
            return random.choice(split_no_obj)
        return

    def get_O_entity_label(self,doi=None,idx=None):
        '''
        get labeled O entities from body. Should get either doi or idx
        :param doi:
        :param idx:
        :return:
        '''
        O_labelled_list=[]
        if doi:
            idx=self.data.index[self.data['doi']==doi].to_list()[0]
        else:
            idx=idx
        paper = paper_pmc(df=self.data,idx_in_df=idx)
        paper.get_content()
        if paper.unclassified_section:
            for head in paper.unclassified_section:
                text=paper.unclassified_section[head]
                extracted_other_text= self.get_O_entity_from_text(text)
                if extracted_other_text:
                    O_labelled_list.append(extracted_other_text)
            return list(set(O_labelled_list))
        else:
            return []
