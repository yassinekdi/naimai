from semanticscholar import SemanticScholar
from tqdm.notebook import tqdm
import time
import random

class EGU_crawler:
    def __init__(self, dois):
        self.docs = {'title': [], 'authors': [], 'date': [], 'field_paper': [], "abstract": [], "doi": [],
                     "numCitedBy": [], "numCiting": []}
        self.docs['doi'] = dois

    def get_authors(self, authors_list):
        return ', '.join([elt['name'] for elt in authors_list])

    def correct_result(self, result):
        if result:
            return result
        else:
            return ""

    def get_docs(self,t_min=1, t_max=4,show_tqdm=True):
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
                    else:
                        dois_to_remove.append(doi)
                else:
                    dois_to_remove.append(doi)
            except:
                dois_to_remove.append(doi)

        for doi in dois_to_remove:
            self.docs['doi'].remove(doi)