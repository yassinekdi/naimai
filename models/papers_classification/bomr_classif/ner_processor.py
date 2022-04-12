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

    def len_intersection_2_ranges(self,rang1: range, rang2: range) -> int:
        '''
        get length of intersection between range1 and range2
        :param rang1: range
        :param rang2:
        :return:
        '''
        xs = set(rang1)
        return len(xs.intersection(rang2))

    def intersection_with_class(self,sentence_range: range, class_ranges: range) -> int:
        '''
        get length of intersection between range of wids on of sentence_range and list of ranges in class ranges
        :param sentence_range:
        :param class_ranges:
        :return:
        '''
        sum = 0
        for rg in class_ranges:
            sum += self.len_intersection_2_ranges(rg, sentence_range)
        return sum

    def get_range_wids_labels(self) -> dict:
        '''
        get, for each label, list of ranges between start word ids and last word ids
        :return:
        '''
        labels = self.df['class'].unique().tolist()
        range_wids_labels = {elt: [] for elt in labels}
        for _, elt in self.df.iterrows():
            class_ = elt['class']
            start, end = elt['start'], elt['end']
            range_wids_labels[class_].append(range(start, end))
        return range_wids_labels

    def get_label_with_most_overlap(self,sentence_range_wids: range, range_wids_labels: dict) -> str:
        '''
        find label with most overlap : with the higher intersection between class ranges and sentence range of wids.
        :return:
        '''
        overlaps = {}
        for cls in range_wids_labels:
            class_ranges = range_wids_labels[cls]
            overlaps[cls]= self.intersection_with_class(sentence_range_wids,class_ranges)
        highest_overlap = max(overlaps.values())
        highest_class = [elt for elt in overlaps if overlaps[elt]==highest_overlap]
        return highest_class[0]
