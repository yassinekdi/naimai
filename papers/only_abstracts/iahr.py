from naimai.papers.raw import papers, paper_base

class paper_iahr(paper_base):
    def __init__(self,df,idx_in_df):
        super().__init__(df,idx_in_df)

    def get_doi(self):
        self.doi=self.paper_infos['webpage']

    def get_fields(self):
        self.fields = [self.paper_infos['field'],]

    def get_journal(self):
        self.Journal =  'IAHR'

class papers_iahr(papers):
    def __init__(self, papers_path,database,nlp=None):
        super().__init__(papers_path,database,nlp) # loading self.naimai_dois & other attributes

    def add_paper(self,idx_in_data,check_database=True):
        new_paper = paper_iahr(df=self.data,
                                idx_in_df=idx_in_data)
        new_paper.get_doi()
        if new_paper.doi:
            new_paper.get_Title()
            if check_database:
                is_in_database_condition = new_paper.is_in_database(self.naimai_dois)
            else:
                is_in_database_condition = False
            if not is_in_database_condition:
                new_paper.get_Abstract()
                if len(new_paper.Abstract.split())>5:
                    new_paper.get_fields()
                    new_paper.get_journal()
                    new_paper.get_Authors()
                    new_paper.get_year()
                    new_paper.replace_abbreviations()
                    self.elements[new_paper.doi] = new_paper.save_dict()
                    self.naimai_dois.append(new_paper.doi)