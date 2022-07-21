import re
import random
import os
from tqdm.notebook import tqdm
from naimai.utils.general import load_gzip, save_gzip
from naimai.constants.paths import naimai_dois_path
from naimai.models.abbreviation import extract_abbreviation_definition_pairs
from naimai.processing import TextCleaner

class paper_base:
    def __init__(self):
        self.pdf_path=''
        self.database='raw'
        self.file_name = ''
        self.raw_text = ''
        self.fields = []
        self.numCitedBy = .5
        self.numCiting = .5
        self.Introduction = ''
        self.Journal = ''
        self.highlights = []
        self.Abstract = ''
        # self.is_Abstract_structured=False
        self.Conclusion = ''
        self.Keywords = ''
        self.Authors = ''
        self.Title = ''
        self.year = 999
        self.References = []
        self.Emails = []
        self.doi = ''


    def get_abbreviations_dict(self):
        abstract_abbrevs = extract_abbreviation_definition_pairs(doc_text=self.Abstract)
        intro_abbrevs = extract_abbreviation_definition_pairs(doc_text=self.Introduction)
        conclusion_abbrevs = extract_abbreviation_definition_pairs(doc_text=self.Conclusion)
        abstract_abbrevs.update(intro_abbrevs)
        abstract_abbrevs.update(conclusion_abbrevs)

        corrected_abbrevs = {}
        for k in abstract_abbrevs:
            corrected_abbrevs[' ' + k] = ' ' + abstract_abbrevs[k] + ' ' + '(' + k + ')'
        return corrected_abbrevs

    def clean_text(self,text):
        '''
        clean the text based on TextCleaner object
        :param text:
        :return:
        '''
        cleaner = TextCleaner(text)
        cleaner.clean()
        return cleaner.cleaned_text

    def is_in_database(self,list_dois):
        if self.doi in list_dois:
            return True
        return False

    def is_paper_english(self,nlp) -> bool:
        '''
        Detect language if paper language is english based on its title.
        :return:
        '''
        if self.Title:
            title_nlp = nlp(self.Title)
            language_score=title_nlp._.language
            condition_english = (language_score['language']=='en') and (language_score['score']>0.7)
            if condition_english:
                return True
            else:
                return False
        # lang = language_score['language']
        # score = language_score['score']
        # print(f'Langage {lang} - Score {score}')
        return True

    def save_dict(self):
        attr_to_save = ['doi', 'Authors', 'year','database','fields','Abstract','Keywords', 'Title','numCitedBy','numCiting', 'highlights','Journal']
        paper_to_save = {key: self.__dict__[key] for key in attr_to_save}
        return paper_to_save




class paper_full_base(paper_base):
    def __init__(self):
        super().__init__()
        self.Introduction = {}
        self.Methods = {}
        self.Results = {}
        self.unclassified_section = {}

    def get_abbreviations_dict(self):
        '''
        get all abbreviations of the papers in Introduction & Methods sections.
        :return:
        '''
        abstract_abbrevs={}
        if isinstance(self.Abstract,str):
            abstract_abbrevs = extract_abbreviation_definition_pairs(doc_text=self.Abstract)
        elif isinstance(self.Abstract,dict):
            for elt in self.Abstract:
                abstract_abbrevs = extract_abbreviation_definition_pairs(doc_text=self.Abstract[elt])
                abstract_abbrevs.update(abstract_abbrevs)

        for elt in self.Introduction:
            intro_abbrevs = extract_abbreviation_definition_pairs(doc_text=self.Introduction[elt])
            abstract_abbrevs.update(intro_abbrevs)
        for elt in self.Methods:
            methods_abbrevs = extract_abbreviation_definition_pairs(doc_text=self.Methods[elt])
            abstract_abbrevs.update(methods_abbrevs)

        corrected_abbrevs = {}
        for k in abstract_abbrevs:
            corrected_abbrevs[' ' + k] = ' ' + abstract_abbrevs[k] + ' ' + '(' + k + ')'
        return corrected_abbrevs

    def is_paper_english(self,nlp) -> bool:
        '''
        Detect language if paper language is english based on its title.
        :return:
        '''
        if self.Title:
            title_nlp = nlp(self.Title)
            language_score=title_nlp._.language
            condition_english = (language_score['language']=='en') and (language_score['score']>0.7)
            if condition_english:
                return True
        lang = language_score['language']
        score = language_score['score']
        print(f'Langage {lang} - Score {score}')
        return False

    def save_dict(self):
        attr_to_save = ['doi', 'Authors', 'year','database','fields','Abstract','Keywords','Title','numCitedBy','numCiting', 'Journal']
        paper_to_save = {key: self.__dict__[key] for key in attr_to_save}
        return paper_to_save


class papers:
    def __init__(self):
        self.elements = {}
        self.path_errors_log = 'drive/MyDrive/MyProject/errors_log/'
        self.database='mine'
        if os.path.exists(naimai_dois_path):
            self.naimai_dois = load_gzip(naimai_dois_path)
        else:
            print('No naimai dois..')
            self.naimai_dois=[]

    def __len__(self):
        return len(self.elements.keys())

    def __setitem__(self, key, value):
        self.elements[key] = value

    def __getitem__(self, item):
        return self.elements[item]

    def random_papers(self,k=3, seed=None):
        elts = list(self.elements)
        random.seed(seed)
        rds = random.sample(elts, k)
        papers_list = [self.elements[el] for el in rds]
        return papers_list

    # @paper_reading_error_log_decorator
    # def add_paper(self,portion=1/6,use_ocr=False):
    #         new_paper = paper()
    #         new_paper.read_pdf(use_ocr)
    #         if new_paper.converted_text:
    #             new_paper.get_Introduction(portion=portion)
    #             new_paper.get_Abstract()
    #             # new_paper.get_authors()
    #             new_paper.get_Conclusion()
    #             new_paper.get_year()
    #             new_paper.get_kwords()
    #             self.elements[new_paper.file_name] = new_paper.save_dict()
    #         else:
    #             self.elements[new_paper.file_name] = "USE OCR"


    def get_papers(self,portion=1/6,list_files=[],path_chunks='',use_ocr=False):
        all_files=[]
        if list_files:
            all_files = list_files

        idx=0
        for file_name in tqdm(all_files):
            if re.findall('pdf', file_name, flags=re.I):
                self.add_paper(portion=portion,use_ocr=use_ocr)
                if idx % 500 == 0 and path_chunks:
                    print('  Saving papers - idx {} for filename {}'.format(idx, file_name))
                    self.save(path_chunks)
                idx+=1
        print('Objs problem exported in objectives_pbs.txt')

    def save_elements(self, file_dir,update=False):
        papers_to_save = self.__dict__['elements']
        if update and os.path.exists(file_dir):
            loaded_papers = load_gzip(file_dir)
            loaded_papers.update(papers_to_save)
            save_gzip(file_dir,loaded_papers)
        else:
            save_gzip(file_dir,papers_to_save)


    def update_naimai_dois(self):
        if self.naimai_dois:
            save_gzip(naimai_dois_path,self.naimai_dois)
#
# class papers_full(papers):
#     def __init__(self):
#         super().__init__()
#         self.naimai_dois=[]