import numpy as np
import pandas as pd
import ast
import re

from naimai.constants.regex import regex_background, regex_objective,regex_methods,regex_results, regex_objectives

class OMRData:
    '''
      Construct data for OMR classification, based on pmc dataframes :
          1. transform structured abstracts to the BOMR structure {Background:.., Objective:.., Methods:.., Results:..}
          2. move objective phrases in background (if exist) to objective section in BOMR
          3. convert BOMR dict to df
          4. Stack & Format the data in the input format for the classifiers
      '''
    def __init__(self, data_df=None,path_data=''):
        if path_data:
            data = pd.read_csv(path_data)
        else:
            data = data_df
        data['is_structured'] = data['abstract'].apply(self.is_structured)
        self.data = data[['doi', 'abstract']][data['is_structured'] == True] # only structured abstracts & dois are selected
        self.transformed_data = None
        self.BOMR_class_num = {'b':0,'o':1,'m':2,'r':3}

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
        return BOMR

    def abstract2BOMR(self,abstract_dict):
        '''
        map abstract dict to BOMR dict
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
            BOMR[head]=BOMR[head].strip()
        BOMR_corrected = self.correct_BOMR(BOMR) #move obj phrases from background to objective
        return BOMR_corrected
    def get_headers_order(self,order='BOMR'):
        '''
        give list of BOMR headers following one of 3 orders :
            1. BOMR
            2. OBMR
            3. MOBR
        :param order:
        :return: list of headers
        '''
        if order=='BOMR':
            return ['background', 'objectives', 'methods', 'results']
        elif order=='OBMR':
            return ['objectives','background','methods','results']
        elif order=='MOBR':
            return ['methods','objectives','background','results']
        else:
            print('not well written.., returned the default BOMR')
            return ['background', 'objectives', 'methods', 'results']

    def BOMR2dict_data(self,BOMR,id_BOMR,order='BOMR'):
        '''
        transforms BOMR dictionary into data disctionary following the given order. Default order : BOMR
        :param BOMR: BOMR dictionary
        :param id_BOMR: id of the BOMR
        :param order: string : BOMR, OBMR or MOBR
        :return:
        '''
        headers= self.get_headers_order(order=order)
        dict_data = {'id': [], 'text': [], 'start': [], 'end': [], 'predict_string': [], 'class': [], 'class_num': []}

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
                dict_data['predict_string'].append(words_ids)
                dict_data['class'].append(head)
                first_class_letter = head[0]
                dict_data['class_num'].append(self.BOMR_class_num[first_class_letter])

                id_str_start+=len(BOMR[head])
                last_word_id=words_ids[-1]

        dict_data['id'] = [id_BOMR]*len(dict_data['text'])
        return dict_data

    def data2BOMR_df(self):
        '''
        convert the data df to BOMR dataframe, which is the input to models..
        :return:
        '''
        list_BOMR_dicts = list(self.data['abstract'].apply(self.abstract2BOMR))
        list_dois = list(self.data['doi'])
        list_bomr_dfs = []
        for bomr,doi in zip(list_BOMR_dicts,list_dois):
            dict_data = self.BOMR2dict_data(bomr,doi)
            df = pd.DataFrame(dict_data)
            list_bomr_dfs.append(df)
        dfs_concatenated = pd.concat(list_bomr_dfs, ignore_index=True)
        dfs_concatenated['start']= dfs_concatenated['start'].astype(int)
        dfs_concatenated['end']= dfs_concatenated['end'].astype(int)
        dfs_concatenated['class_num']= dfs_concatenated['class_num'].astype(int)
        self.transformed_data= dfs_concatenated