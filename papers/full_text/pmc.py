import ast
import re
import pandas as pd
from tqdm.notebook import tqdm

from naimai.papers.raw import papers, paper_full_base
from naimai.constants.paths import path_open_citations
from naimai.constants.regex import regex_spaced_chars
from naimai.utils.regex import multiple_replace
from naimai.utils.general import get_soup

class paper_pmc(paper_full_base):
    def __init__(self ,df ,idx_in_df):
        super().__init__()
        self.database ="pmc"
        self.paper_infos = df.iloc[idx_in_df,:]

    def get_doi(self):
        self.doi = self.paper_infos['doi']

    def get_Abstract(self,stacked=True):
        '''
        clean & stack (if stacked=True) abstract elements into one text.
        The spaced abstract case (a b s t r a c t..) is considered. if stacked = False, it returns abstract as dictionary
        :return:
        '''
        abstract_dict_str = self.paper_infos['abstract']
        abstract_dict = ast.literal_eval(abstract_dict_str)
        if stacked:
            abstract_dict = {elt: abstract_dict[elt] for elt in abstract_dict if not re.findall('electronic', elt, re.I)}
            abstract = ' '.join([elt for elt2 in list(abstract_dict.values()) for elt in elt2])
            no_space = re.findall('\w\w',abstract)
            if no_space: # normal case
                self.Abstract = abstract.replace('-\n', '').replace('\n', ' ')
            else: #spaced abstract, we "despace" 2 times
                despacing1 = re.sub(regex_spaced_chars, r'\1\2', abstract)
                self.Abstract = re.sub(regex_spaced_chars, r'\1\2', despacing1).replace('\n',' ')

            # clean abstract
            text = re.sub('abstract', '',self.Abstract).strip()
            cleaned_text = self.clean_text(text)
            self.Abstract = cleaned_text
        else:
            result = {elt: ' '.join(abstract_dict[elt]) for elt in abstract_dict}
            result_txt = ''
            for elt in result:
                result_txt+=' '+ elt+': '+result[elt]
            return result_txt.strip()

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

    def get_Introduction(self,body,imr_sections):
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

    def get_Methods(self,body,imr_sections):
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

    def get_Results(self, body, imr_sections):
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

    def get_content(self):
        '''
        get body infos and decompose it to abstract and IMR sections
        :return:
        '''
        body = self.get_body()
        headers = list(body.keys())
        self.get_Abstract()
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


    def replace_abbreviations(self):
        abbreviations_dict = self.get_abbreviations_dict()
        if abbreviations_dict:
            self.Abstract = multiple_replace(abbreviations_dict, self.Abstract)
            for elt in self.Introduction:
                self.Introduction[elt] = multiple_replace(abbreviations_dict, self.Introduction[elt])
            for elt in self.Methods:
                self.Methods[elt] = multiple_replace(abbreviations_dict, self.Methods[elt])
            for elt in self.Results:
                self.Results[elt] = multiple_replace(abbreviations_dict, self.Results[elt])
            self.Title = multiple_replace(abbreviations_dict, self.Title)

class papers_pmc(papers):
    def __init__(self, papers_path):
        super().__init__() # loading self.naimai_dois & other attributes
        self.naimai_dois = []
        self.data = pd.read_csv(papers_path)
        print('Len data : ', len(self.data))

    def add_paper(self,idx_in_data):
            new_paper = paper_pmc(df=self.data,
                                    idx_in_df=idx_in_data)
            new_paper.get_doi()
            # if not new_paper.is_in_database(self.naimai_dois):
            # self.naimai_dois.append(new_paper.doi)
            new_paper.get_Title()
            new_paper.get_Authors()
            new_paper.get_journal()
            new_paper.get_year()
            new_paper.get_content()
            new_paper.replace_abbreviations()
            new_paper.get_numCitedBy()
            self.elements[new_paper.doi] = new_paper.save_dict()


    # @update_naimai_dois
    def get_papers(self):
        for idx,_ in tqdm(self.data.iterrows(),total=len(self.data)):
            self.add_paper(idx_in_data=idx)