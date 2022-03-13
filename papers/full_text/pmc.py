import ast
import re

from papers.raw import papers, paper_base
from naimai.constants.paths import path_open_citations
from naimai.utils.regex import multiple_replace
from naimai.utils.general import get_soup

class paper_pmc(paper_base):
    def __init__(self ,df ,idx_in_df):
        super().__init__()
        self.database ="pmc"
        self.paper_infos = df.iloc[idx_in_df,:]


    def get_doi(self):
        self.doi = self.paper_infos['doi']

    def get_Abstract(self):
        '''
        stack abstract elements into one text
        :return:
        '''
        abstract_dict_str = self.paper_infos['abstract']
        abstract_dict = ast.literal_eval(abstract_dict_str)
        abstract = ' '.join([elt for elt2 in list(abstract_dict.values()) for elt in elt2])
        self.Abstract = abstract.replace('-\n', '').replace('\n', ' ')

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

    def headers2imr(self,headers):
        '''
        get list of headers of the paper and convert it to imr sections
        :param headers:
        :return: {'abstract': [..], 'introduction': [..], 'method': [..], 'results':[..], 'rest': [..]}
        '''
        imr_sections_dict = {'abstract':[], 'introduction':[],'methods':[],'results':[],'rest':[]}
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

    def get_Abstract_extra(self,body,imr_sections):
        '''
        Add text before introduction to abstract section
        :param body:
        :param imr_sections:
        :return:
        '''
        headers = imr_sections['abstract']
        if headers:
            for head in headers:
                self.Abstract += ' ' + body[head]
        self.Abstract = self.Abstract.strip()

    def get_Introduction(self,body,imr_sections):
        '''
        get introductions elements & stack them in introduction section
        :param body:
        :param imr_sections:
        :return:
        '''
        headers = imr_sections['introduction']
        if headers:
            for head in headers:
                self.Introduction += ' ' + body[head]

        self.Introduction = self.Introduction.strip()

    def get_Methods(self,body,imr_sections):
        '''
        get methods elements & stack them in method section
        :param body:
        :param imr_sections:
        :return:
        '''
        headers = imr_sections['methods']
        if headers:
            for head in headers:
                self.Methods += ' ' + body[head]

        self.Methods = self.Methods.strip()

    def get_Results(self, body, imr_sections):
        '''
        get methods elements & stack them in method section
        :param body:
        :param imr_sections:
        :return:
        '''
        headers = imr_sections['results']
        if headers:
            for head in headers:
                self.Results += ' ' + body[head]

        self.Results = self.Results.strip()

    def get_content(self):
        '''
        get body infos and decompose it to abstract and IMR sections
        :return:
        '''
        body = self.get_body()
        headers = list(body.keys())
        imr_sections = self.headers2imr(headers)

        self.get_Abstract_extra(body=body,imr_sections=imr_sections)
        self.get_Introduction(body=body,imr_sections=imr_sections)
        self.get_Methods(body=body,imr_sections=imr_sections)
        self.get_Results(body=body,imr_sections=imr_sections)

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
            self.Introduction = multiple_replace(abbreviations_dict, self.Introduction)
            self.Methods = multiple_replace(abbreviations_dict, self.Methods)
            self.Results = multiple_replace(abbreviations_dict, self.Results)
            self.Title = multiple_replace(abbreviations_dict, self.Title)
