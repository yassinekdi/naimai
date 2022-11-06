from naimai.papers.raw import papers, paper_base

class paper_egu(paper_base):
    def __init__(self,df,idx_in_df):
        super().__init__(df,idx_in_df)

    def get_doi(self):
        if str(self.paper_infos['doi'])=='nan':
            self.doi=''
        else:
            self.doi = self.paper_infos['doi'].replace('https://doi.org/','')

    def get_fields(self):
        self.fields = [self.paper_infos['field'],]

    def get_journal(self):
        self.Journal =  'Atmospheric Chemistry and Physics'


class papers_egu(papers):
    def __init__(self,papers_path,database,nlp=None):
        super().__init__(papers_path,database,nlp) # loading self.naimai_dois & other attributes

    def add_paper(self,idx_in_data):
            new_paper = paper_egu(df=self.data,
                                    idx_in_df=idx_in_data)
            new_paper.get_doi()
            if new_paper.doi:
                new_paper.get_Title()
                if not new_paper.is_in_database(self.naimai_dois):
                    new_paper.get_Abstract()
                    if len(new_paper.Abstract.split())>5:
                        new_paper.get_fields()
                        new_paper.get_journal()
                        new_paper.get_Authors()
                        new_paper.get_year()
                        new_paper.replace_abbreviations()
                        new_paper.get_numCitedBy()
                        self.elements[new_paper.doi] = new_paper.save_dict()
                        self.naimai_dois.append(new_paper.doi)

