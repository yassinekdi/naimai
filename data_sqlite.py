import sqlite3

class SQLiteManager:
  def __init__(self,path_db):
    connexion = sqlite3.connect(path_db)
    self.cursor = connexion.cursor()

  def get_by_multiple_ids(self,list_ids):
    tuple_ids = tuple([elt+1 for elt in list_ids])
    self.cursor.execute("SELECT * FROM all_papers WHERE rowid IN {}".format(tuple_ids))
    return self.cursor.fetchall()

  def get_by_multiple_fnames(self,fnames,year_from=0,year_to=3000):
    tuples_fnames = tuple(fnames)
    self.cursor.execute("SELECT * FROM all_papers WHERE fname IN {} AND \
     year >= {} AND year <= {} ".format(tuples_fnames, year_from,year_to))
    return self.cursor.fetchall()