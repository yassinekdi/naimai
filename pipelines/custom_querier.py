from naimai.constants.regex import regex_and_operators,regex_or_operators,regex_exact_match
from naimai.utils.general import get_root_fname
from naimai.models.papers_classification.tfidf import tfidf_model
import re

class CustomQuerier:
  def __init__(self,produced_papers,encoder,custom_index):
    self.encoder=encoder
    self.produced_papers = produced_papers
    self.custom_index=custom_index

  def get_corresponding_fnames(self, wanted_papers_fnames: list, root_papers_fnames: list) -> list:
    '''
    find original fnames based on root fnames
    '''
    root_fnames = [elt.replace('_objectives', '') for elt in root_papers_fnames]

    results_papers_fnames = []
    for elt in root_fnames:
      for idx, pap in enumerate(wanted_papers_fnames):
        if elt in pap:
          results_papers_fnames.append(wanted_papers_fnames[idx])

    return results_papers_fnames


  def filter_by_numCitedBy(self, fnames: list) -> list:
    '''
    Rank first papers papers using numCitedBy parameter
    :param papers:
    :return:
    '''
    nb_papers_ranked_CitedBy = 3
    for fname in fnames:
      paper = self.produced_papers[fname]
      if 'numCitedBy' not in paper:
        paper['numCitedBy']=.5

    # keys = list(papers.keys())
    papers_to_rank = [self.produced_papers[fname] for fname in fnames[:nb_papers_ranked_CitedBy]]
    papers_to_rank.sort(key=lambda x: float(x['numCitedBy']), reverse=True)
    fnames_ranked = [elt['fname'] for elt in papers_to_rank]
    rest_of_papers_fnames = [fname for fname in fnames[nb_papers_ranked_CitedBy:]]
    papers_ranked = fnames_ranked + rest_of_papers_fnames
    return papers_ranked


  def get_query_type(self,query):
    '''
    determine the query type : AND op (0), OR op (1), exact match (2),semantic (3)
    '''
    AND_operator = re.findall(regex_and_operators,query)
    OR_operator =  re.findall(regex_or_operators,query)
    exact_match=re.findall(regex_exact_match, query)

    if AND_operator:
      return 0 
    if OR_operator:
      return 1 
    if exact_match:
      return 2 
    return 3


  def keywords_in_paper(self,keywords: list,operator: int,paper: dict) -> bool:
    '''
    check if keywords are in papers following an operator
    '''   
    fname = list(paper.keys())[0]

    if '_objectives' in fname:
      info = self.produced_papers[fname]['messages'] + ' '+ self.produced_papers[fname]['title']
    else:
      info = self.produced_papers[fname]['messages'] 

    if operator==0: #AND operator 
      pattern = ''.join([f'(?:.*{kw})'for kw in keywords])
      if re.findall(pattern,info,flags=re.I):
        return True

    elif operator==1: #OR operator
      pattern = re.compile('|'.join(keywords))
      if re.findall(pattern,info,flags=re.I):
        return True

    elif operator==2: # exact match
      for query in keywords:
        if re.findall(query,info):
          return True

    return False 


  def get_papers_with_exact_match(self,query: str) -> list:
    '''
    find papers for a query with exact match
    '''
    keywords = re.findall(regex_exact_match, query)
    selected_papers_fnames = []

    for fname in self.produced_papers:
      paper = self.produced_papers[fname]
      if self.keywords_in_paper(keywords=keywords,operator=2,paper=paper):
        selected_papers_fnames.append(fname)
    return selected_papers_fnames


  def get_papers_with_OR_operator(self,query: str) -> list:
    '''
    find papers for a query with or operator
    '''
    keywords = [elt.strip() for elt in re.split(regex_or_operators,query)]
    selected_papers_fnames = []

    for fname in self.produced_papers:
      paper = self.produced_papers[fname]
      if self.keywords_in_paper(keywords=keywords,operator=1,paper=paper):
        selected_papers_fnames.append(fname)
    return selected_papers_fnames


  def get_papers_with_AND_operator(self,query: str) -> list:
    '''
    find papers for a query with and operator
    '''

    keywords = [elt.strip() for elt in re.split(regex_and_operators,query)]
    selected_papers_fnames = []

    for fname in self.produced_papers:
      paper = self.produced_papers[fname]
      if self.keywords_in_paper(keywords=keywords,operator=0,paper=paper):
        selected_papers_fnames.append(fname)
    return selected_papers_fnames


  def get_papers_with_semantics(self,query: str, top_n=30) -> list:
    '''
    find papers using tf idf model
    '''

    tf = tfidf_model(query=query, papers=self.produced_papers)
    selected_papers_fnames = tf.get_similar_fnames(top_n=top_n)
    return selected_papers_fnames
   

  def get_all_similar_papers(self, query: str, query_type: int) -> list:
    '''
    Get all similar papers & their fnames based on the query and query type
    :param query:
    :return:
    '''
    selected_papers_fnames = []
    if query_type==0: #AND operator
      selected_papers_fnames= self.get_papers_with_AND_operator(query)

    elif query_type==1: #OR operator
      selected_papers_fnames= self.get_papers_with_OR_operator(query)

    elif query_type==2: #exact match
      selected_papers_fnames= self.get_papers_with_exact_match(query)

    elif query_type==3: #semantics
      selected_papers_fnames= self.get_papers_with_semantics(query)

    return selected_papers_fnames

  def filter_by_year(self,fnames: list, year_from=0,year_to=3000) -> list:
    '''
    filter list of fnames papers by years range
    '''

    filtered_fnames=[]
    for fname in fnames:
      paper = self.produced_papers[fname]
      if (int(paper['year'])>=year_from) and (int(paper['year']<=year_to)):
        filtered_fnames.append(fname)

    return filtered_fnames


  def search(self, query: str, year_from=0, year_to=3000) -> list:
    '''
    1. Get query type : AND op (0), OR op (1), exact match (2),semantic (3)
    2. Get all similar papers and their fnames 
    3. Apply filters : need root fname:
      3.1 Apply years range filter 
      3.2 Apply OMR filter (not yet)
      3.3 Apply numCitedBy filter
    4. Find corresponding papers to root fnames ranked
    :param query:
    :param top_n:
    :param year_from:
    :param year_to:
    :return:
    '''

    # 1. Get query type : AND op (0), OR op (1), exact match (2),semantic (3)
    query_type = self.get_query_type(query)

    # 2. Get all similar papers and their fnames using tf idf
    selected_papers_fnames = self.get_all_similar_papers(query, query_type)

    # 3. Apply filters : need root fname:
    root_fnames = [get_root_fname(fname) for fname in selected_papers_fnames]

      # 3.1 Apply years range filter 
    root_fnames_year_filtered = self.filter_by_year(root_fnames, year_from=year_from,year_to=year_to)

      # 3.2 Apply OMR filter

      # 3.3 Apply numCitedBy filter
    root_fnames_numCitedBy_filtered = self.filter_by_numCitedBy(root_fnames_year_filtered)

    #4. Find corresponding papers to root fnames ranked 
    corresponding_fnames = self.get_corresponding_fnames(selected_papers_fnames, root_fnames_numCitedBy_filtered)

    return corresponding_fnames