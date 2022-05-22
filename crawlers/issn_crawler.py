from crossref.restful import Journals
from semanticscholar import SemanticScholar
from tqdm.notebook import tqdm
import time
import random


class ISSN_crawler:
    def __init__(self, issn, field_issn):
        self.issn = issn
        self.field_issn = field_issn
        self.docs = {'title': [], 'authors': [], 'date': [], 'field_paper': [], "abstract": [], "doi": [],
                     "numCitedBy": [], "numCiting": [], "field_issn": []}

    def get_dois(self,idx_start,idx_finish):
        journals = Journals()
        works = journals.works(self.issn)
        for elt in works.select('DOI'):
          try:
            self.docs["doi"].append(elt["DOI"])
          except:
            pass
        self.docs["doi"] = self.docs["doi"][idx_start:idx_finish]
        print('Len dois : ', len(self.docs['doi']))

    def get_authors(self, authors_list):
        return ', '.join([elt['name'] for elt in authors_list])

    def correct_result(self, result):
        if result:
            return result
        else:
            return ""

    def get_docs(self,idx_start=0, idx_finish=-1,t_min=2, t_max=5,show_tqdm=True):
        if not self.docs['doi']:
            self.get_dois(idx_start, idx_finish)
        sch = SemanticScholar(timeout=20)
        dois_to_remove = []
        if show_tqdm:
            range_=tqdm(self.docs['doi'])
        else:
            range_ = self.docs['doi']
        for doi in range_:
            try:
                paper = sch.paper(doi)
                slp = random.randint(t_min, t_max)
                time.sleep(slp)

                if paper:
                    abstract = self.correct_result(paper["abstract"])
                    if abstract:
                        self.docs['title'].append(self.correct_result(paper["title"]))
                        authors = self.get_authors(paper["authors"])
                        self.docs['authors'].append(self.correct_result(authors))
                        self.docs['date'].append(self.correct_result(paper["year"]))
                        if paper["fieldsOfStudy"]:
                            field = ", ".join(paper["fieldsOfStudy"])
                        else:
                            field = ""
                        self.docs['field_paper'].append(field)
                        self.docs['abstract'].append(abstract)
                        self.docs['numCitedBy'].append(self.correct_result(paper["numCitedBy"]))
                        self.docs['numCiting'].append(self.correct_result(paper["numCiting"]))
                        self.docs['field_issn'].append(self.correct_result(self.field_issn))
                    else:
                        dois_to_remove.append(doi)
                else:
                    dois_to_remove.append(doi)
            except:
                dois_to_remove.append(doi)

        for doi in dois_to_remove:
            self.docs['doi'].remove(doi)
