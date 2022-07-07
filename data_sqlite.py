import sqlite3
from ast import literal_eval
from naimai.utils.general import clean_lst

class SQLiteManager:
  def __init__(self,path_db: str):
    connexion = sqlite3.connect(path_db)
    self.cursor = connexion.cursor()

  def get_by_multiple_ids(self,list_ids:  list)-> dict:
    '''
      get papers using list of ids
    '''
    tuple_ids = tuple([elt+1 for elt in list_ids])
    self.cursor.execute("SELECT * FROM all_papers WHERE rowid IN {}".format(tuple_ids))
    results = self.cursor.fetchall()
    dict_result = {elt[10]: self.to_dict(elt) for elt in results}
    return dict_result

  def get_by_query(self, query: str) -> dict:
    '''
    get papers that contains query in title or message
    :param query:
    :return:
    '''
    query_command = '%' + query + '%'
    qry = (query_command,query_command)
    self.cursor.execute("SELECT * FROM all_papers WHERE title LIKE ? OR messages LIKE ? ",qry)
    result = self.cursor.fetchall()
    papers_list = clean_lst(result)
    dict_result = {elt[10]: self.to_dict(elt) for elt in papers_list}
    return dict_result

  def get_by_fname(self,fname: str)-> dict:
    '''
      fine fname
    '''
    self.cursor.execute("SELECT * FROM all_papers WHERE fname = ?", (fname,))
    result = self.cursor.fetchone()
    return self.to_dict(result)

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


  def get_by_multiple_fnames(self,fnames: list,year_from=0,year_to=3000) -> dict:
    '''
      get papers between range of years using list of filenames
    '''
    fnames = clean_lst(fnames)
    results = {}
    for fname in fnames:
      paper = self.get_by_fname(fname)
      results[fname]= paper
    return results

  def to_dict(self,sql_result: tuple) -> dict:
    '''
      transform sql results (in tuple format) to dictionary format
    '''
    cols = ['website','year', 'database', 'messages', 'reported', 'title', 'journal',
    'authors', 'numCitedBy', 'fname']

    dict_result = {}
    if sql_result:
      for col,val in zip(cols,sql_result[1:]):
        if val:
          if val[0]=='[':
            val = literal_eval(val)
          dict_result[col]= val
      return dict_result
    return {}
