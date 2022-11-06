from naimai.papers.raw import papers, paper_base

class paper_issn(paper_base):
    def __init__(self,df,idx_in_df):
        super().__init__(df,idx_in_df)

    def get_fields(self):
        self.fields = [self.paper_infos['field_paper'], self.paper_infos['field_issn']]


    def get_journal(self):
        self.Journal =  self.paper_infos['field_issn']


class papers_issn(papers):
    def __init__(self,papers_path,database,nlp=None):
        super().__init__(papers_path,database,nlp) # loading self.naimai_dois & other attributes

    def add_paper(self,idx_in_data):
            new_paper = paper_issn(df=self.data,
                                    idx_in_df=idx_in_data)
            new_paper.get_doi()
            new_paper.get_Title()
            if not new_paper.is_in_database(self.naimai_dois):
                new_paper.get_Abstract()
                new_paper.get_fields()
                new_paper.get_journal()
                new_paper.get_Authors()
                new_paper.get_year()
                new_paper.replace_abbreviations()
                new_paper.get_numCitedBy()
                self.elements[new_paper.doi] = new_paper.save_dict()
                self.naimai_dois.append(new_paper.doi)

