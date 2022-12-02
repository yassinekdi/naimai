from naimai.constants.regex import regex_and_operators,regex_exact_match
from naimai.models.papers_classification.tfidf import tfidf_model
from naimai.utils.regex import lemmatize_query
from .base import BaseQuerier
import re

class CustomQuerier(BaseQuerier):
  def __init__(self,produced_papers):
    super().__init__(is_custom=True)
    self.produced_papers = produced_papers

  def keywords_in_paper(self,keywords: list,operator: int,paper: dict) -> bool:
    '''
    check if keywords are in papers following an operator
    '''   
    fname = list(paper.keys())[0]

    if '_objectives' in fname:
      info = '. '.join(self.produced_papers[fname]['messages']) + ' '+ self.produced_papers[fname]['title']
    else:
      info = '. '.join(self.produced_papers[fname]['messages'])

    if operator==self.search_operators['multiple']: #AND operator
      pattern = ''.join([f'(?:.*{kw})'for kw in keywords])
      if re.findall(pattern,info,flags=re.I):
        return True

    elif operator==self.search_operators['match']: # exact match
      for query in keywords:
        if re.findall(query,info):
          return True

    return False 

  def get_papers_with_exact_match(self,query: str,year_from=0,year_to=3000,top_n=200) -> tuple:
    '''
    find papers for a query with exact match
    '''
    keywords = re.findall(regex_exact_match, query)
    selected_papers_fnames = []
    selected_papers = []

    for fname in self.produced_papers:
      paper = {fname : self.produced_papers[fname]}
      if self.keywords_in_paper(keywords=keywords,operator=2,paper=paper):
        selected_papers_fnames.append(fname)
        selected_papers.append(paper)
    return selected_papers, selected_papers_fnames


  def get_papers_with_AND_operator(self,query: str,year_from=0,year_to=3000,top_n=200) -> tuple:
    '''
    find papers for a query with and operator
    '''

    keywords = [elt.strip() for elt in re.split(regex_and_operators,query)]
    selected_papers_fnames = []
    selected_papers = []

    for fname in self.produced_papers:
      paper = {fname : self.produced_papers[fname]}
      if self.keywords_in_paper(keywords=keywords,operator=0,paper=paper):
        selected_papers_fnames.append(fname)
        selected_papers.append(paper)
    return selected_papers, selected_papers_fnames


  def get_papers_for_tfidf_semantics(self,query: str, year_from=0, year_to=3000, top_n=30) -> tuple:
    '''
    find papers using tf idf model
    '''

    lemmatized_query = ' '.join(lemmatize_query(self.nlp, query)).strip()
    tf = tfidf_model(query=lemmatized_query, papers=self.produced_papers)
    selected_papers_fnames,_ = tf.get_similar_fnames(top_n=top_n)
    selected_papers = [self.produced_papers[fn] for fn in selected_papers_fnames]
    return selected_papers, selected_papers_fnames