import sqlite3
import re
from naimai.constants.regex import regex_and_operators,regex_or_operators,regex_exact_match
from ast import literal_eval
from naimai.utils.general import clean_lst

class SQLiteManager:
  def __init__(self,path_db: str):
    connexion = sqlite3.connect(path_db)
    self.cursor = connexion.cursor()

  def get_by_multiple_ids(self,list_ids:  list, year_from=0, year_to=3000,)-> dict:
    '''
      get papers using list of ids
    '''
    tuple_ids = tuple([elt+1 for elt in list_ids])
    self.cursor.execute("SELECT website,year, database, messages, reported, title, journal, authors, numCitedBy, fname, allauthors FROM all_papers WHERE rowid IN {}".format(tuple_ids))
    results = self.cursor.fetchall()
    dict_result = {elt[9]: self.to_dict(elt) for elt in results}
    # filter by years range
    dict_result = {elt: dict_result[elt] for elt in dict_result if dict_result[elt]['year']>year_from and dict_result[elt]['year']<year_to}
    return dict_result

  def search_with_exact_match(self, query: str, year_from=0, year_to=3000,top_n=5) -> dict:
    '''
    find papers for a query with exact match
    '''
    keywords = re.findall(regex_exact_match, query)
    similar_papers = {}

    for word in keywords:
      papers = self.get_by_query(word,year_from=year_from,year_to=year_to,top_n=top_n)
      similar_papers.update(papers)

    return similar_papers

  def search_with_OR_operator(self, query: str, year_from=0, year_to=3000,top_n=5) -> dict:
    '''
    find papers that contains at least one of the query keywords. Similar to many exact match..
    '''
    keywords = [elt.strip() for elt in re.split(regex_or_operators, query)]
    similar_papers = {}

    for word in keywords:
      papers = self.get_by_query(word, year_from=year_from,year_to=year_to,top_n=top_n)
      similar_papers.update(papers)

    return similar_papers

  def search_with_AND_operator(self, query: str, year_from=0, year_to=3000,top_n=5) -> dict:
    '''
    find papers that contains all the query keywords : start by using or operator for first
    key word, then filter papers with all key words
    '''
    keywords = [elt.strip() for elt in re.split(regex_and_operators, query)]
    similar_papers = {}

    kword1 = keywords[0]
    # get papers with only kword1
    papers_with_kword1 = self.get_by_query(kword1,year_from=year_from,year_to=year_to,top_n=top_n)

    # filter the papers having other keywords as well
    pattern = ''.join([f'(?:.*{kw})' for kw in keywords[1:]])
    for fname in papers_with_kword1:
      # get text of paper
      if '_objectives' in fname:
        info = '. '.join(papers_with_kword1[fname]['messages']) + ' ' + papers_with_kword1[fname]['title']
      else:
        info = '. '.join(papers_with_kword1[fname]['messages'])

      # check if contains all keywords
      if re.findall(pattern, info, flags=re.I):
        similar_papers.update({fname: papers_with_kword1[fname]})

    return similar_papers

  def get_by_lemmatized_query(self, lemmatized_query: list, year_from=0, year_to=3000, top_n=5) -> dict:
    '''
    get all papers in range of years using a lemmatized query. The difference with get_by_query is that the lemmatized query is in list format!
    :return:
    '''

    params_lemmatized_query = ['%'+w+'%' for w in lemmatized_query]

    params=[year_to,year_from]+[params_lemmatized_query[i//2] for i in range(len(params_lemmatized_query)*2)]
    kwords_in_msg = ' AND '.join(['(title LIKE ? OR messages LIKE ?)' for _ in lemmatized_query])
    command= "SELECT website,year, database, messages, reported, title, journal, authors, numCitedBy, fname, allauthors FROM all_papers WHERE (year < ? AND year > ?) AND "+kwords_in_msg

    self.cursor.execute(command, params)
    # result = self.cursor.fetchmany(top_n)
    result = self.cursor.fetchall()
    papers_list = clean_lst(result)
    dict_result = {elt[9]: self.to_dict(elt) for elt in papers_list}
    if len(lemmatized_query)==1:
      query = lemmatized_query[0]
      filtered_dict_result = self.filter_papers(query,dict_result)
      return filtered_dict_result
    return dict_result

  def filter_papers(self,query: str,papers: dict) -> dict:
    '''
    filter papers when the query is in the word
    :param query:
    :param papers:
    :return:
    '''
    pattern = '[^a-zA-Z]' + query
    new_papers = {}
    for fname in papers:
      messages = papers[fname]['messages']
      for text in messages:
        if re.findall(pattern,text,re.I):
          new_papers[fname]=papers[fname]
          break
    return new_papers

  def get_by_query(self, query: str, year_from=0, year_to=3000,top_n=5) -> dict:
    '''
    get papers that contains query in title or message. Here, the input query is not lemmatized.
    :param query:
    :return:
    '''
    query_command = '%' + query + '%'
    qry = (year_to,year_from,query_command,query_command)
    self.cursor.execute("SELECT website,year, database, messages, reported, title, journal, authors, numCitedBy, fname, allauthors FROM all_papers WHERE (year < ? AND year > ?) AND (title LIKE ? OR messages LIKE ?) ",qry)
    # result = self.cursor.fetchall()
    result = self.cursor.fetchmany(top_n)
    papers_list = clean_lst(result)
    dict_result = {elt[9]: self.to_dict(elt) for elt in papers_list}
    filtered_dict_result = self.filter_papers(query,dict_result)

    return filtered_dict_result

  def get_by_fname(self, fname: str, year_from=0, year_to=3000) -> dict:
    '''
      find paper by fname
    '''
    self.cursor.execute(
      "SELECT website,year, database, messages, reported, title, journal, authors, numCitedBy, fname, allauthors FROM all_papers WHERE fname = ?",
      (fname,))
    result = self.cursor.fetchone()
    dict_result = self.to_dict(result)
    if fname.endswith('_objectives'):
      if 'year' in dict_result:
        if (int(dict_result['year']) >= year_from) and (int(dict_result['year']) <= year_to):
          return dict_result
      return {}
    return dict_result

  def get_omr_dics(self,fname: str) -> dict:
    '''
    for fname, get obj, methods & results dict
    '''
    paper_name = '_'.join(fname.split('_')[:-1])
    omr_fnames = [paper_name+'_objectives', paper_name+'_methods',paper_name+'_results']

    result = {}
    for fname in omr_fnames:
      paper = self.get_by_fname(fname)
      result[fname]= paper
    return result


  # def get_by_multiple_fnames(self,fnames: list,year_from=0,year_to=3000) -> dict:
  #   '''
  #     get papers between range of years using list of filenames
  #   '''
  #   params = [year_to,year_from] + clean_lst(fnames)
  #   ln = len(fnames)
  #   conditions = '('+ ' OR '.join(["fname = ?"] * ln)  + ')'
  #   command = "SELECT website,year, database, messages, reported, title, journal, authors, numCitedBy, fname, allauthors FROM all_papers WHERE (year < ? AND year > ?) AND " + conditions
  #   self.cursor.execute(command, params)
  #   list_papers = self.cursor.fetchall()
  #   dict_result = {elt[9]: self.to_dict(elt) for elt in list_papers}
  #   return dict_result


  def to_dict(self,sql_result: tuple) -> dict:
    '''
      transform sql results (in tuple format) to dictionary format
    '''
    cols = ['website','year', 'database', 'messages', 'reported', 'title', 'journal',
    'authors', 'numCitedBy', 'fname','allauthors']

    dict_result = {}
    if sql_result:
      for col,val in zip(cols,sql_result):
        if val:
          try:
            if val[0]=='[' and val[-1]==']':
              val = literal_eval(val)
            dict_result[col]= val
          except:
            pass
      return dict_result
    return {}
