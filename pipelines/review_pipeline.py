from paper2.decorators import review_paper_error_log_decorator
from paper2.models.text_generation.paper2reported import Paper2Reported
import spacy
from paper2.constants import nlp_vocab
import re

class ReviewPipeline:
    def __init__(self ,model ,all_papers, field, topn):
        self.similar_papers =[]
        self.model = model
        self.field=field
        self.topn = topn
        self.all_papers =all_papers
        self.nlp = spacy.load(nlp_vocab)
        self.paper_cited = []
        self.iter_max = topn +7

    # def search_papers(self, query):
    #     result = self.model.sentence_in_docs(query,topn=self.iter_max)
    #     similar_papers_fnames = [elt[0] for elt in result]
    #     return similar_papers_fnames

    # @review_paper_error_log_decorator
    # def review_paper(self, pap, client, review_nb):
    #     review = Paper2Reported(pap,
    #                             field=self.field,
    #                             client=client,
    #                             nlp=self.nlp,)
    #
    #     review.generate(uploaded=self.uploaded, review_nb=review_nb)
    #     if review.reported:
    #         return review.reported
    #     return

    # def get_similar_papers(self ,fname_list):
    #     self.similar_papers = [self.all_papers['elements'][fname] for fname in fname_list]

    def review_query(self, query,client):
        review_nb = 0
        review_nb_list=[]
        fnames =self.search_papers(query)
        self.get_similar_papers(fnames)
        len_similar_papers=len(self.similar_papers)
        reviews =[]
        without_ref_list = []
        iter=0
        while review_nb <self.topn and iter < min(self.iter_max, len_similar_papers):
            pap = self.similar_papers[iter]
            reviewed = self.review_paper(pap, client, review_nb)
            if reviewed:
                without_ref = re.sub('<b>.*</b>','',reviewed)
                without_ref= without_ref[1:]

            if reviewed and without_ref not in without_ref_list:
                reviews.append(reviewed)
                without_ref_list.append(without_ref)
                self.paper_cited.append(pap['file_name'])
                review_nb +=1
                if review_nb == 1:
                    review_nb_list.append(0)
                else:
                    review_nb_list.append(review_nb)
            iter +=1
        if reviews:
            return ' '.join(reviews)
        else:
            return None