import os
from tqdm.notebook import tqdm
from naimai.constants.paths import path_dispatched, path_formatted, path_produced
from naimai.utils.general import load_gzip
from naimai.utils.regex import get_ref_url
import shutil
import matplotlib.pyplot as plt
import re

class Zone:
    def __init__(self, zone_path, zone_name):
        self.elements = {}
        self.zone_path = zone_path
        self.zone_name = zone_name

    def get_papers(self, field, fname, verbose=True):
        '''
        load database
        :param database:
        :return:
        '''
        path_db = os.path.join(self.zone_path,field,fname)
        data=load_gzip(path_db)
        if verbose:
            print('Len data: ', len(data))
        return data

    def get_elements(self):
        if self.zone_path:
            elements = os.listdir(self.zone_path)
            for elt in elements:
                path_elt = os.path.join(self.zone_path, elt)
                if os.path.isdir(path_elt):
                    self.elements[elt] = os.listdir(path_elt)
                else:
                    self.elements[elt] = ''

    def create_fields(self, fields_names):
        for field in fields_names:
            path = os.path.join(self.zone_path, field)
            os.mkdir(path)

    def reset_all(self):
        '''
        clear the zone
        :return:
        '''
        elements = os.listdir(self.zone_path)
        for elt in elements:
            path = os.path.join(self.zone_path, elt)
            if os.path.isdir(path):
                os.rmdir(path)
            else:
                os.remove(path)

    def reset_all_elements(self):
        '''
        clear all elements (folders) of the zone
        :return:
        '''
        for element in self.elements:
            self.reset_element(element)

    def reset_element(self, element):
        '''
        clear the elements of the input element (field/folder)
        :param element: field/folder of the zone
        :return:
        '''
        if element in self.elements:
            path_element = os.path.join(self.zone_path, element)
            if os.path.isdir(path_element):
                files = os.listdir(path_element)
                for f in files:
                    path = os.path.join(path_element, f)
                    if os.path.isfile(path):
                        os.remove(path)
                    elif os.path.isdir(path):
                        shutil.rmtree(path)
            elif os.path.isfile(path_element):
                os.remove(path_element)
        else:
            print('{} is not an element in {} zone'.format(element, self.zone_name))


class Dispatched_Zone(Zone):
    def __init__(self):
        super().__init__(zone_path=path_dispatched, zone_name='dispatched')
        self.get_elements()

    def get_field(self,field,verbose=True):
        '''
        load database
        :param database:
        :return:
        '''
        path_field = os.path.join(self.zone_path,field)
        all_papers = os.listdir(path_field)
        paths_papers = [os.path.join(path_field,pap) for pap in all_papers]
        data_list=[]
        for path_db,paper in zip(paths_papers, all_papers):
            data=load_gzip(path_db)
            data_list.append(data)
            if verbose:
                print(f'paper {paper} - Len data: {len(data)}')
        return data_list

    def reset_allpapers_elt(self,all_papers):
        '''
        reset 'all_papers' in all fields
        :param all_papers:
        :return:
        '''
        fields = list(self.elements)
        for field in fields:
            path = os.path.join(self.zone_path,field,all_papers)
            if os.path.isfile(path):
                os.remove(path)


    def plot_distribution(self, verbose=False):
        fields = list(self.elements)
        lens = []
        for field in fields:
            data_list = self.get_field(field=field, verbose=verbose)
            len_field = sum([len(elt) for elt in data_list])
            lens.append(len_field)

        x,y = fields, lens
        plt.figure(figsize=(10, 8))
        plt.rcParams.update({'font.size': 17})
        plt.barh(x, y, alpha=.5)
        plt.xlabel('N° of papers', fontsize=20)
        plt.xticks(fontsize=16)
        plt.yticks(fontsize=16)
        plt.ylabel('Field', fontsize=20)
        for ind, val in enumerate(y):
            plt.text(val + 3, ind - .25, str(val))

class Formatted_Zone(Zone):
    def __init__(self):
        super().__init__(zone_path=path_formatted, zone_name='formatted')
        self.get_elements()

    def get_database(self,database):
        '''
        load database
        :param database:
        :return:
        '''
        path_db = os.path.join(self.zone_path,database)
        data=load_gzip(path_db)
        print('Len data: ', len(data))
        return data

class Production_Zone(Zone):
    def __init__(self):
        super().__init__(zone_path=path_produced, zone_name='production')
        self.get_elements()

    def clean_papers(self,field,fname):
        papers = self.get_papers(field,fname)
        new_papers = self.remove_empty_elts(papers)
        new_papers = self.correct_years(new_papers)
        new_papers = self.add_numCitedBy(field,fname,new_papers)
        print('Pmc websites are not taken here!')
        return new_papers

    def remove_empty_elts(self,papers):
        '''
        remove empty dictionaries from all_papers dict
        :param papers:
        :return:
        '''
        cleaned_paps = {}
        for fname in papers:
            paper = papers[fname]
            for key in paper:
                if paper[key]:
                    cleaned_paps[fname] = papers[fname]
                    break
        return cleaned_paps

    def correct_years(self,papers):
        '''
        correct some years wrongly saved: in format of xxxx.0
        :param papers:
        :return:
        '''
        new_papers = papers.copy()
        for fname in new_papers:
            if '_objectives' in fname:
                try:
                    new_papers[fname]['year'] = int(new_papers[fname]['year'])
                    new_papers[fname]['authors'] = re.sub('(\d)\.\d', r'\g<1>', new_papers[fname]['authors'])
                except:
                    print('problem in ', fname)
                if new_papers[fname]['reported']:
                    new_papers[fname]['reported'] = re.sub('(\d)\.\d', r'\g<1>', new_papers[fname]['reported'])
        return new_papers

    def add_numCitedBy(self,field,papers_name: str, produced_papers):
        '''
        add numCitedBy parameter in produced papers
        :param field:
        :param papers:
        :return:
        '''
        # get dispatched papers
        dispatched_papers = self.get_papers(path_dispatched,field,papers_name)

        # add numCitedBy
        for key in tqdm(dispatched_papers):
            numCitedBy = dispatched_papers[key]['numCitedBy']

            key_produced = key+'_objective'
            if key_produced in produced_papers:
                produced_papers[key_produced]['numCitedBy'] = numCitedBy

        return produced_papers

    def correct_pmc_websites(self,papers):
        '''
        some pmc papers websites were not correctly considered..
        :param papers:
        :return:
        '''
        for key in papers:
            if '_objectives' in key:
                papers[key]['website'] = get_ref_url(papers)
        return papers


