'''
Since some elsevier open papers could not be processed with papers class (in papers/raw.py), many methods are overwritten in
paper_elsevier and papers_elsevier.

[Documentation here can be more detailed if needed]
'''

import os
import json
from tqdm.notebook import tqdm
from collections import Counter
import re
import pandas as pd
import ast

from naimai.utils.general import get_soup
from naimai.constants.fields import fields_codes_elsevier
from naimai.constants.paths import codes_fields_path, path_open_citations
from naimai.papers.raw import paper_base,papers
from naimai.utils.regex import multiple_replace
from naimai.decorators import update_naimai_dois

class elsevier_data:
  def __init__(self,myfield_dict):
    self.files_path = 'json/json/'
    self.all_files = os.listdir(self.files_path)
    self.files_codes = {}
    self.files_fields = {}
    self.myfield = myfield_dict

  def file_nb2data(self,nb):
    '''
    convert file_nb to content
    :param nb: nb of file (int)
    :return:
    '''
    file_path = os.path.join(self.files_path,self.all_files[nb])
    with open(file_path) as jf:
      data = json.load(jf)
    return data

  def file_nb2code(self,file_nb):
    '''
    convert file_nb to its elsevier codes
    :param file_nb: nb of file (int)
    :return:
    '''
    file_path = os.path.join(self.files_path,self.all_files[file_nb])
    with open(file_path) as jf:
      data = json.load(jf)
    return data['metadata']['asjc']

  def get_files_codes(self):
    '''
    for each file, get its elsevier codes
    :return:
    '''
    for nb in tqdm(range(len(self.all_files))):
      self.files_codes[nb]=self.file_nb2code(nb)

  def is_value_in_codes(self, list_codes, value):
    '''
    verify if code in list of codes (lst)
    :param list_codes: list of codes (list)
    :param value: code (str)
    :return:
    '''
    value = int(value)
    lst_split=[elt.split('-') for elt in list_codes]
    for elt in lst_split:
      if len(elt)>1:
        min_,max_ = int(elt[0]), int(elt[1])
        if value in range(min_, max_ + 1):
          return True
      else:
        if int(elt[0])==value:
          return True
    return False

  def codes2field(self, codes_lst):
    '''
    convert list of codes to the correct field of my fields
    :param codes_lst: list of codes (list)
    :return:
    '''
    result = []
    for key,val in self.myfield.items():
      for code in codes_lst:
        if self.is_value_in_codes(val, code):
          result.append(key)
          break
    return result


  def get_files_fields(self):
    '''
    get the correct field for all the files
    :return:
    '''
    all_files_len = len(self.all_files)
    for file_nb in tqdm(range(all_files_len)):
      code = self.file_nb2code(file_nb)
      self.files_fields[file_nb]= self.codes2field(code)

  def get_files_distribution(self):
    '''
    get the files distribution over my fields
    :return:
    '''
    if self.files_fields:
      result = []
      for val in self.files_fields.values():
        result+=val
      return Counter(result)
    return


class paper_elsevier(paper_base):
    def __init__(self, file_nb,json_data):
        super().__init__()
        self.file_name=file_nb
        self.json_data = json_data
        self.database = 'elsevier_kaggle'
        self.highlights_in = None
        self.doi = ''
        self.highlights = []

    def replace_abbreviations(self):
        abbreviations_dict = self.get_abbreviations_dict()
        if abbreviations_dict:
            self.Abstract = multiple_replace(abbreviations_dict, self.Abstract)
            self.Introduction = multiple_replace(abbreviations_dict, self.Introduction)
            self.Title = multiple_replace(abbreviations_dict, self.Title)
            self.Keywords = multiple_replace(abbreviations_dict, self.Keywords)
            self.highlights = [multiple_replace(abbreviations_dict, elt) for elt in self.highlights]

    def get_Abstract(self):
        if 'abstract' in self.json_data.keys():
            self.Abstract = self.json_data['abstract']

    def get_numCitedBy(self):
        if self.doi:
            path = path_open_citations + self.doi
            soup = get_soup(path)
            soup_list = ast.literal_eval(soup.text)
            if isinstance(soup_list,list):
                self.numCitedBy = len(soup_list)

    def get_highlights(self):
        if 'author_highlights' in self.json_data.keys():
            self.highlights_in = True
            self.highlights += [elt['sentence'] for elt in self.json_data['author_highlights']]
        else:
            self.highlights_in = False

    def title_sentence_from_elt(self, elt):
        result = ' '
        if 'title' in elt.keys():
            result += elt['title'] + '; '

        if 'sentence' in elt.keys():
            result += elt['sentence']
        return result

    def introduction_from_elt(self,elt):
        if 'title' in elt.keys():
            if re.findall('introduction', elt['title'], re.I):
               return elt['sentence']
        return
    def get_Introduction(self):
        if 'body_text' in self.json_data.keys():
            for elt in self.json_data['body_text']:
                stc = self.introduction_from_elt(elt)
                if stc:
                    self.Introduction += stc + ' '


    def conclusion_from_elt(self,elt):
        if 'title' in elt.keys():
            if re.findall('conclusion', elt['title'], re.I):
               return elt['sentence']
        return
    def get_Conslusion(self):
        if 'body_text' in self.json_data.keys():
            for elt in self.json_data['body_text']:
                stc = self.conclusion_from_elt(elt)
                if stc:
                    self.Conclusion += stc + ' '

    def get_raw_text(self):
        if 'body_text' in self.json_data.keys():
            for elt in self.json_data['body_text']:
                self.raw_text += self.title_sentence_from_elt(elt)

    def get_Title(self):
        if 'title' in self.json_data['metadata'].keys():
            self.Title = self.json_data['metadata']['title']

    def code2subfields(self,code,df_codes):
        return list(df_codes[df_codes['Code'] == int(code)][['Field', 'Subject area']].values[0])

    def get_fields(self,field=''):
        result = [field,]
        codes_fields_df = pd.read_excel(codes_fields_path)
        paper_codes = self.json_data['metadata']['asjc']
        for code in paper_codes:
            result += self.code2subfields(code, codes_fields_df)
        self.fields = list(set(result))

    def get_Authors(self):
        if 'authors' in self.json_data['metadata'].keys():
            first, last = '', ''
            authors_data = self.json_data['metadata']['authors']
            for elt in authors_data:
                if elt['first']:
                    first = elt['first']
                if elt['last']:
                    last = elt['last']
                self.Authors += ' ' + first+ ' '+ last +','
            if self.Authors[-1]==',':
                self.Authors= self.Authors[:-1]
        self.Authors = self.Authors.strip()

    def get_kwords(self):
        if 'keywords' in self.json_data['metadata'].keys():
            self.Keywords = ', '.join(self.json_data['metadata']['keywords'])

    def get_journal(self):
        if 'doi' in self.json_data['metadata'].keys():
            self.Journal = self.json_data['metadata']['issn']

    def get_doi(self):
        if 'doi' in self.json_data['metadata'].keys():
            self.doi = self.json_data['metadata']['doi']

    def get_year(self):
        if 'pub_year' in self.json_data['metadata'].keys():
            self.year = self.json_data['metadata']['pub_year']


class papers_elsevier(papers):
    def __init__(self,elsevier_data_obj=None):
        super().__init__() # loading self.naimai_dois & other attributes
        self.fields_dict = fields_codes_elsevier
        self.elsevier_data_obj = elsevier_data_obj
        self.files = []


    def get_all_files(self):
      self.elsevier_data_obj = elsevier_data(myfield_dict=fields_codes_elsevier)
      self.elsevier_data_obj.get_files_fields()

    def get_fields_files(self, field,reset=True):
      if reset:
          self.files=[]
      for k,v in self.elsevier_data_obj.files_fields.items():
        if field in v:
          self.files.append(k)

    def add_papers(self,paper_nb,field):
        json_data=self.elsevier_data_obj.file_nb2data(paper_nb)
        new_paper = paper_elsevier(file_nb=paper_nb,json_data=json_data)
        new_paper.get_doi()
        if not new_paper.is_in_database(self.naimai_dois):
             new_paper.get_fields(field)
             new_paper.get_Abstract()
             new_paper.get_Title()
             new_paper.get_Authors()
             new_paper.get_journal()
             new_paper.get_kwords()
             new_paper.get_year()
             new_paper.get_highlights()
             new_paper.replace_abbreviations()
             new_paper.get_numCitedBy()
             self.elements[new_paper.doi] = new_paper.save_dict()
             self.naimai_dois.append(new_paper.doi)

        else:
            pass
            # print('DOI {} already exists..'.format(new_paper.doi))



    @update_naimai_dois
    def get_papers(self,field, reset=True,update_dois=False,idx_start=0,idx_finish=-1):
        if reset:
            self.elements={}
        if not self.elsevier_data_obj:
            print('>> Getting all papers')
            self.get_all_files()
        self.get_fields_files(field)
        fles = self.files[idx_start:idx_finish]
        for f in tqdm(fles):
            try:
                self.add_papers(paper_nb=f, field=field)
            except:
                print('problem in paper ', f)
