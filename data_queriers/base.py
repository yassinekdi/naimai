from naimai.constants.paths import path_produced
from naimai.utils.general import clean_lst
from .sqlite_manager import SQLiteManager
import os
import re

class BaseQuerier:
  def __init__(self,field, encoder=None, field_index=None, nlp=None):
    self.encoder = encoder
    self.field = field
    self.field_index = field_index
    path_sqlite = os.path.join(path_produced, self.field, 'all_papers_sqlite')
    self.sql_manager = SQLiteManager(path_sqlite)
    self.nlp = nlp



  def remove_duplicated_fnames(self,list_fnames):
      '''
      remove duplicated fnames in list of results to keep only one paper per result
      :param list_fnames:
      :return:
      '''
      pattern = '_objectives|_methods|_results'
      only_fnames = [re.sub(pattern, '', elt) for elt in list_fnames]
      filtered_fnames = clean_lst(only_fnames)

      idxs_to_keep = []
      for fname in filtered_fnames:
        idxs_to_keep.append([idx for idx, elt in enumerate(list_fnames) if fname in elt][0])

      non_duplicated_fnames = [list_fnames[idx] for idx in idxs_to_keep]
      return non_duplicated_fnames


  def get_corresponding_papers(self, wanted_papers_fnames: list, root_papers_fnames: list) -> list:
    '''
    XXX
    :param wanted_papers_fnames:
    :param root_papers_fnames:
    :return:
    '''
    root_fnames = [elt.replace('_objectives', '') for elt in root_papers_fnames]

    results_papers_fnames = []
    for elt in root_fnames:
      for idx, pap in enumerate(wanted_papers_fnames):
        if elt in pap:
          results_papers_fnames.append(wanted_papers_fnames[idx])

    return results_papers_fnames

  def rank_papers_with_numCitedBy(self, papers: dict,len_query: int) -> list:
    '''
    Rank first papers papers using numCitedBy parameter. if len query > 3 : rank only first 5
    :param papers:
    :return:
    '''
    if len_query>3:
      nb_papers_ranked_CitedBy = 5
    else:
      nb_papers_ranked_CitedBy = len(papers)
    for fname in papers:
      if 'numCitedBy' not in papers[fname]:
        papers[fname]['numCitedBy'] = .5
    keys = list(papers.keys())
    papers_to_rank = [papers[fname] for fname in keys[:nb_papers_ranked_CitedBy]]
    papers_to_rank.sort(key=lambda x: float(x['numCitedBy']), reverse=True)
    fnames_ranked = [elt['fname'] for elt in papers_to_rank]
    rest_of_papers_fnames = [fname for fname in keys[nb_papers_ranked_CitedBy:]]
    papers_ranked = fnames_ranked + rest_of_papers_fnames
    return papers_ranked


