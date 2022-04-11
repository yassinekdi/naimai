import ast
import re
import pandas as pd
from tqdm.notebook import tqdm
from spacy_langdetect import LanguageDetector
import spacy

from naimai.papers.raw import papers, paper_full_base
from naimai.constants.paths import path_open_citations
from naimai.constants.regex import regex_spaced_chars,regex_keywords
from naimai.constants.nlp import nlp_vocab
from naimai.utils.regex import multiple_replace
from naimai.utils.general import get_soup


class paper_pmc(paper_full_base):
    def __init__(self ,df ,idx_in_df):
        super().__init__()
        self.database ="pmc"
        self.paper_infos = df.iloc[idx_in_df,:]

    def get_doi(self) -> str:
        self.doi = self.paper_infos['doi']

    def get_Keywords_from_dict_abstract(self) -> str:
        '''
        get keywords from abstract when it's in a dict format & filter from abstract
        :return:
        '''
        for elt in self.Abstract:
            txt = self.Abstract[elt]
            keywords_in_txt = re.findall(regex_keywords, txt, re.I)
            if keywords_in_txt:
                self.Keywords = keywords_in_txt[0].strip()
                regex_filter = 'key\s?words:\s?' + self.Keywords
                self.Abstract[elt] = re.sub(regex_filter,'',txt,flags=re.I).strip()

    def get_Keywords_from_str_abstract(self)-> str:
        '''
        get keywords from abstract when it's in str format & filter from abstract
        :return:
        '''
        txt = self.Abstract
        keywords_in_txt = re.findall(regex_keywords, txt, re.I)
        if keywords_in_txt:
            self.Keywords = keywords_in_txt[0].strip()
            regex_filter = 'key\s?words:\s?' + self.Keywords
            self.Abstract = re.sub(regex_filter, '', txt, flags=re.I).strip()

    def get_Keywords(self) -> str:
        '''
        Get keywords from abstracts elements & remove them from abstract
        :return:
        '''
        if isinstance(self.Abstract,dict):
            self.get_Keywords_from_dict_abstract()
        elif isinstance(self.Abstract,str):
            self.get_Keywords_from_str_abstract()


    def get_Abstract(self,stacked=True,dict_format=False) -> str:
        '''
        clean & stack (if stacked=True) abstract elements into one text & get Keywords from abstract.
        The spaced abstract case (a b s t r a c t..) is considered. if stacked = False, it puts the abstract elements in
        str format. It can returns in dict format if dict_format=True
        :return:
        '''
        abstract_dict_str = self.paper_infos['abstract']
        abstract_dict = ast.literal_eval(abstract_dict_str)
        if 'text' not in abstract_dict.keys():
            abstract_dict = {elt: ' '.join(abstract_dict[elt]) for elt in abstract_dict}

        for elt in abstract_dict:
            clean1=re.sub('abstract', '',abstract_dict[elt], flags=re.I).strip()
            clean2 = self.clean_text(clean1)
            abstract_dict[elt]=clean2

        if stacked:
            abstract = ' '.join([elt for elt2 in list(abstract_dict.values()) for elt in elt2])
            no_space = re.findall('\w\w',abstract)
            if no_space: # normal case
                self.Abstract = abstract.replace('-\n', '').replace('\n', ' ')
            else: #spaced abstract, we "despace" 2 times
                despacing1 = re.sub(regex_spaced_chars, r'\1\2', abstract)
                self.Abstract = re.sub(regex_spaced_chars, r'\1\2', despacing1).replace('\n',' ')

        else:
            # result = {elt: ' '.join(abstract_dict[elt]) for elt in abstract_dict}
            if dict_format:
                self.Abstract = abstract_dict
            else:
                result_txt = ''
                for elt in abstract_dict:
                    result_txt+=' '+ elt+': '+abstract_dict[elt]
                self.Abstract= result_txt.strip()
        self.get_Keywords()
    def get_Title(self):
        self.Title = self.paper_infos['title'].replace('-\n', '').replace('\n', ' ')

    def get_Authors(self):
        authors_list_str = self.paper_infos['authors']
        authors_list = ast.literal_eval(authors_list_str)
        self.Authors = ', '.join(authors_list)

    def get_year(self):
        self.year = self.paper_infos['year']

    def get_journal(self):
        self.Journal =  self.paper_infos['journal']

    def get_body(self):
        body_dict_str = self.paper_infos['body']
        body_dict = ast.literal_eval(body_dict_str)
        return body_dict

    def headers2imr(self,headers: list) -> dict:
        '''
        get list of headers of the paper and convert it to imr sections
        :param headers:
        :return: {'abstract': [..], 'introduction': [..], 'method': [..], 'results':[..], 'rest': [..]}
        '''
        imr_sections_dict = {'abstract':[], 'introduction':[],'methods':[],'results':[],'references':[]}
        imr_sections_list = list(imr_sections_dict)
        imr_rgx = ['abstract', 'introduction', 'methods?', 'results?|discussion',
                       'references|funding|disclosures|acknowledgment']
        idx_section = 0
        for elt in headers:
            pointer = imr_sections_list[idx_section]
            nextp = imr_sections_list[idx_section + 1]
            try:
                nextp2 = imr_sections_list[idx_section + 2]
            except:
                pass
            nextp_rgx = imr_rgx[idx_section + 1]
            pattern_next = re.compile(nextp_rgx, flags=re.I)
            pattern_next2 = re.compile(nextp2, flags=re.I)
            if re.findall(pattern_next, elt):
                if idx_section + 2 < len(imr_sections_list):
                    imr_sections_dict[nextp] += [elt]
                    idx_section += 1
                else:
                    imr_sections_dict[nextp] += [elt]
            elif re.findall(pattern_next2, elt):
                imr_sections_dict[nextp2] += [elt]
                idx_section += 2
            else:
                imr_sections_dict[pointer] += [elt]
        return imr_sections_dict

    def get_abstract_extra(self, body, imr_sections):
        '''
        Clean & Add text before introduction to unclassified section
        :param body:
        :param imr_sections:
        :return:
        '''
        headers = imr_sections['abstract']
        if headers:
            for head in headers:
                text = ' '.join(body[head])
                cleaned_text = self.clean_text(text)
                self.unclassified_section[head] =cleaned_text

    def get_Introduction(self,body,imr_sections) -> dict:
        '''
        get introductions elements & clean & stack them in introduction section
        :param body:
        :param imr_sections:
        :return:
        '''
        headers = imr_sections['introduction']
        if headers:
            for head in headers:
                text= ' '.join(body[head])
                cleaned_text = self.clean_text(text)
                self.Introduction[head] =cleaned_text

    def get_Methods(self,body,imr_sections) -> dict:
        '''
        get methods elements & clean & stack them in method section
        :param body:
        :param imr_sections:
        :return:
        '''
        headers = imr_sections['methods']
        if headers:
            for head in headers:
                text = ' '.join(body[head])
                cleaned_text = self.clean_text(text)
                self.Methods[head]= cleaned_text

    def get_Results(self, body, imr_sections) -> dict:
        '''
        get methods elements & clean & stack them in method section
        :param body:
        :param imr_sections:
        :return:
        '''
        headers = imr_sections['results']
        if headers:
            for head in headers:
                text = ' '.join(body[head])
                cleaned_text = self.clean_text(text)
                self.Results[head] = cleaned_text

    def get_non_imrad_content(self,body):
        '''
        when the format is not imrad, we gather everything in unclassified section
        :param body:
        :return:
        '''
        headers = list(body)
        for head in headers:
            text = ' '.join(body[head])
            cleaned_text = self.clean_text(text)
            self.unclassified_section[head] = cleaned_text

    def get_content(self,stacked_abstract=True,abstract_dict_format=False):
        '''
        get body infos and decompose it to abstract and IMR sections
        :return:
        '''
        body = self.get_body()
        headers = list(body.keys())
        self.get_Abstract(stacked=stacked_abstract,dict_format=abstract_dict_format)
        try:
            imr_sections = self.headers2imr(headers)
            self.get_abstract_extra(body=body, imr_sections=imr_sections)
            self.get_Introduction(body=body,imr_sections=imr_sections)
            self.get_Methods(body=body,imr_sections=imr_sections)
            self.get_Results(body=body,imr_sections=imr_sections)
        except: #not IMRAD format
            self.get_non_imrad_content(body)



    def get_numCitedBy(self):
        if self.doi!=self.file_name:
            path = path_open_citations + self.doi
            soup = get_soup(path)
            soup_list = ast.literal_eval(soup.text)
            if isinstance(soup_list,list):
                self.numCitedBy = len(soup_list)

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


    def replace_abbreviations(self):
        abbreviations_dict = self.get_abbreviations_dict()
        if abbreviations_dict:
            if isinstance(self.Abstract,str):
                self.Abstract = multiple_replace(abbreviations_dict, self.Abstract)
            elif isinstance(self.Abstract,dict):
                for elt in self.Abstract:
                    self.Abstract[elt] = multiple_replace(abbreviations_dict, self.Abstract[elt])
            for elt in self.Introduction:
                self.Introduction[elt] = multiple_replace(abbreviations_dict, self.Introduction[elt])
            for elt in self.Methods:
                self.Methods[elt] = multiple_replace(abbreviations_dict, self.Methods[elt])
            for elt in self.Results:
                self.Results[elt] = multiple_replace(abbreviations_dict, self.Results[elt])
            self.Title = multiple_replace(abbreviations_dict, self.Title)

class papers_pmc(papers):
    def __init__(self, papers_path,stacked_abstract=True,abstract_dict_format=False,nlp=None):
        super().__init__() # loading self.naimai_dois & other attributes
        self.naimai_dois = []
        self.data = pd.read_csv(papers_path)
        self.stacked_abstract=stacked_abstract
        self.abstract_dict_format=abstract_dict_format
        print('Len data : ', len(self.data))
        if nlp:
            self.nlp = nlp
        else:
            print('Loading nlp vocab..')
            self.nlp = spacy.load(nlp_vocab)
        self.nlp.add_pipe(LanguageDetector(), name='language_detector', last=True)

    def add_paper(self,idx_in_data):
            new_paper = paper_pmc(df=self.data,
                                    idx_in_df=idx_in_data)
            new_paper.get_doi()
            # if not new_paper.is_in_database(self.naimai_dois):
            # self.naimai_dois.append(new_paper.doi)
            new_paper.get_Title()
            if new_paper.is_paper_english(self.nlp):
                new_paper.get_Authors()
                new_paper.get_journal()
                new_paper.get_year()
                new_paper.get_content(stacked_abstract=self.stacked_abstract,
                                      abstract_dict_format=self.abstract_dict_format)
                new_paper.replace_abbreviations()
                new_paper.get_numCitedBy()
                self.elements[new_paper.doi] = new_paper.save_dict()
            else:
                print(f'in Title : {new_paper.Title} - index in data {idx_in_data} is not english..')


    # @update_naimai_dois
    def get_papers(self):
        for idx,_ in tqdm(self.data.iterrows(),total=len(self.data)):
            self.add_paper(idx_in_data=idx)