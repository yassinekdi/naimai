'''
The issn papers could not be processed with papers class (in papers/raw.py) because of the fields and journal data.
So the get_fields and get_journal methods are overwritten in paper_issn class, and the add_paper method is
overwritten in papers_issn to use paper_issn (instead of paper_base).
'''

from naimai.papers.raw import papers, paper_base

class paper_issn(paper_base):
    '''
    Paper class that map a row if the csv file with data about papers to a dictionary.
    '''
    def __init__(self,df,idx_in_df):
        super().__init__(df,idx_in_df)

    def get_fields(self):
        self.fields = [self.paper_infos['field_paper'], self.paper_infos['field_issn']]


    def get_journal(self):
        self.Journal =  self.paper_infos['field_issn']


class papers_issn(papers):
    def __init__(self,papers_path,database,nlp=None):        
        '''
        inherits from the papers class
        :param papers_path: path of the csv file
        :param database: name of the database if all the papers in the csv file are coming from the same source.
        :param nlp:  spaCy nlp pipeline
        '''
        super().__init__(papers_path,database,nlp) # loading self.naimai_dois & other attributes

    def add_paper(self,idx_in_data,check_database=True):
        '''
        Add a paper data as element
        :param idx_in_data: idx of the paper in the csv file
        :param check_database: if True, the paper is not added as element if already contained in the database.
        :return:
        '''
        new_paper = paper_issn(df=self.data,
                                idx_in_df=idx_in_data)
        new_paper.get_doi()
        new_paper.get_Title()
        if check_database:
            is_in_database_condition = new_paper.is_in_database(self.naimai_dois)
        else:
            is_in_database_condition = False
        if not is_in_database_condition:
            new_paper.database = self.database
            new_paper.get_Abstract()
            new_paper.get_fields()
            new_paper.get_journal()
            new_paper.get_Authors()
            new_paper.get_year()
            new_paper.replace_abbreviations()
            new_paper.get_numCitedBy()
            self.elements[new_paper.doi] = new_paper.save_dict()
            self.naimai_dois.append(new_paper.doi)

