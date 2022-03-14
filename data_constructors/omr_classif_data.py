import pandas as pd
import ast
import re

from naimai.constants.regex import regex_background, regex_objective,regex_methods,regex_results, regex_objectives

class OMRData:
    '''
      Construct data for OMR classification, based on pmc dataframes :
          1. transform structured abstracts to the BOMR structure {Background:.., Objective:.., Methods:.., Results:..}
          2. Try to check & reorganize some sentences wrongly classified in the original abstract
          3. Stack the sections with different orders
          4. Format the data in the input format for the classifiers
      '''
    def __init__(self, data_df=None,path_data=''):
        if path_data:
            data = pd.read_csv(path_data)
        else:
            data = data_df
        data['is_structured'] = data['abstract'].apply(self.is_structured)
        self.data = data[['doi', 'abstract']][data['is_structured'] == True] # only structured abstracts & dois are selected
        self.BOMR_class_num = {'B':0,'O':1,'M':2,'R':3}

    def is_structured(self,text):
        '''
        check if abstract is structured
        :param text:
        :return:
        '''
        txt2dic = ast.literal_eval(text)
        if 'text' in txt2dic:
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

    def BOMR2df_data(self,BOMR,order='BOMR'):
        '''
        stack BOMR dictionary following the given order. Default order : BOMR
        :param BOMR: BOMR dictionary
        :param order: string : BOMR, OBMR or MOBR
        :return:
        '''
        headers= self.get_headers_order(order=order)
        stacked = ''
        for head in headers:
            stacked += BOMR[head]
        return stacked
