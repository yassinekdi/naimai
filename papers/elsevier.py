import os
import json
from tqdm.notebook import tqdm
from collections import Counter
import re

from paper2.constants.fields import fields_codes_elsevier
from paper2.papers.raw import paper_base,papers
from paper2.utils import multiple_replace

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
    def __init__(self, file_nb,json_data, obj_classifier_model=None):
        super().__init__(obj_classifier_model)
        self.file_name=file_nb
        self.json_data = json_data
        self.highlights_in = None
        self.doi = ''
        self.authors_highlights = []

    def replace_abbreviations(self):
        abbreviations_dict = self.get_abbreviations_dict()
        if abbreviations_dict:
            self.Abstract = multiple_replace(abbreviations_dict, self.Abstract)
            self.Conclusion = multiple_replace(abbreviations_dict, self.Conclusion)
            self.Introduction = multiple_replace(abbreviations_dict, self.Introduction)
            self.Title = multiple_replace(abbreviations_dict, self.Title)
            self.Keywords = multiple_replace(abbreviations_dict, self.Keywords)
            self.authors_highlights = [multiple_replace(abbreviations_dict, elt) for elt in self.authors_highlights]

    def get_Abstract(self):
        if 'abstract' in self.json_data.keys():
            self.Abstract = self.json_data['abstract']


    def get_highlights(self):
        if 'author_highlights' in self.json_data.keys():
            self.highlights_in = True
            self.authors_highlights += [elt['sentence'] for elt in self.json_data['author_highlights']]
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

    def get_kwords(self):
        if 'keywords' in self.json_data['metadata'].keys():
            self.Keywords = ', '.join(self.json_data['metadata']['keywords'])

    def get_doi(self):
        if 'doi' in self.json_data['metadata'].keys():
            self.doi = self.json_data['metadata']['doi']

    def get_Publication_year(self):
        if 'pub_year' in self.json_data['metadata'].keys():
            self.Publication_year = self.json_data['metadata']['pub_year']


class papers_elsevier(papers):
    def __init__(self,elsevier_data_obj=None,obj_classifier_model=None, author_classifier_model=None,
                 load_obj_classifier_model=True, load_author_classifier_model=False,load_nlp=True):
      super().__init__(obj_classifier_model=obj_classifier_model, author_classifier_model=author_classifier_model,
                       load_obj_classifier_model=load_obj_classifier_model,load_author_classifier_model=load_author_classifier_model,
                       load_nlp=load_nlp)
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

    def add_papers(self,paper_nb,save_dict=True,report=True):
     json_data=self.elsevier_data_obj.file_nb2data(paper_nb)
     new_paper = paper_elsevier(file_nb=paper_nb,json_data=json_data,obj_classifier_model=self.obj_classifier_model)
     new_paper.database= 'elsevier_kaggle'
     new_paper.get_Abstract()
     #new_paper.get_Introduction()
     new_paper.get_Conslusion()
     #new_paper.get_raw_text()
     new_paper.get_Title()
     new_paper.get_Authors()
     new_paper.get_kwords()
     new_paper.get_doi()
     new_paper.get_Publication_year()
     new_paper.replace_abbreviations()
     new_paper.get_highlights()
     new_paper.get_objective_paper(add_sentences=new_paper.authors_highlights)
     if report:
         new_paper.report_objectives()
     if save_dict:
         self.elements[paper_nb] = new_paper.save_paper_for_training()
         self.naimai_elements[paper_nb] = new_paper.save_paper_for_naimai()
     else:
         self.elements[paper_nb] = new_paper


    def get_papers(self,field, save_dict=True,reset=True, report=True):
        if reset:
            self.elements={}
        if not self.elsevier_data_obj:
            print('>> Getting all papers')
            self.get_all_files()
        self.get_fields_files(field)
        for f in tqdm(self.files):
            try:
                self.add_papers(paper_nb=f, save_dict=save_dict,report=report)
            except:
                print('problem in paper ', f)
        print('Objs problem exported in objectives_pbs.txt')
