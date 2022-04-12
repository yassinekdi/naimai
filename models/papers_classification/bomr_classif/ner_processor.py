from naimai.utils.transformers import split_list, list2pstring, get_first_char_id, get_last_char_id
import pandas as pd

class NER_BOMR_processor:
    def __init__(self, text, df):
        self.text = text
        self.df = df

    def process_predictionstring(self, elt) -> list:
        '''
        process predictionstring column to split lists into sequences
        :param elt:
        :return:
        '''
        list_pstring = list(map(int, elt.split()))
        list_processed = split_list(list_pstring)
        return list_processed

    def process_df(self):
        '''
        transform original df into df with splitted predictionstring following sequences
        :return:
        '''
        new_dict = {'class': [], 'new_pstring': []}
        self.df['pstring_processed'] = self.df['predictionstring'].apply(self.process_predictionstring)
        for idx in range(len(self.df)):
            elts = self.df.iloc[idx]
            classe = elts['class']
            new_pstrings = elts['pstring_processed']
            if len(new_pstrings) == 1:
                pstring_elt = new_pstrings[0]
                new_dict['class'].append(classe)
                list_pstring = list2pstring(pstring_elt)
                new_dict['new_pstring'].append(list_pstring)
            else:
                for elt in new_pstrings:
                    if elt:
                        new_dict['class'].append(classe)
                        list_pstring = list2pstring(elt)
                        new_dict['new_pstring'].append(list_pstring)
        self.df = pd.DataFrame(new_dict)

    def add_metadata(self):
        '''
        add start, end, start_char and last_char in columns of df
        :return:
        '''
        self.process_df()
        self.df['start'] = self.df['new_pstring'].apply(lambda x: int(x.split()[0]) - 1)
        self.df['end'] = self.df['new_pstring'].apply(lambda x: int(x.split()[-1]))
        self.df['start_char'] = self.df.apply(get_first_char_id, args=(self.text,), axis=1)
        self.df['last_char'] = self.df.apply(get_last_char_id, args=(self.text,), axis=1)
        self.df = self.df.sort_values(by=['start']).reset_index(drop=True)