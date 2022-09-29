import pickle, gzip, pickletools
import requests
from bs4 import BeautifulSoup
import os
from tqdm.notebook import tqdm
from naimai.constants.paths import naimai_dois_path
import ast
from collections import Counter
import pandas as pd
import re
import time


def load_gzip(path):
    with gzip.open(path, 'rb') as f:
        p = pickle.Unpickler(f)
        return p.load()

def save_gzip(path,obj):
    with gzip.open(path, "wb") as f:
        pickled = pickle.dumps(obj)
        optimized_pickle = pickletools.optimize(pickled)
        f.write(optimized_pickle)

def to_sql(papers,conn):
  print('start..')
  paps_df = pd.DataFrame(papers).T
  print('indexing..')
  paps_df['fname'] = paps_df.index
  paps_df = paps_df.reset_index(drop=True)
  print('filling na..')
  paps_df=paps_df.fillna('')
  paps_df = paps_df.astype(str)
  print('saving..')
  paps_df.to_sql(name='all_papers',con=conn)
  print('done!')


def load_gzip_and_update(paths_fnames):
  zips=[]
  if len(paths_fnames)>1:
      for fname in tqdm(paths_fnames):
        zips.append(load_gzip(fname))
      main_dict = zips[0]
      for elt in zips[1:]:
        main_dict.update(elt)
      return main_dict
  all_paps = load_gzip(paths_fnames[0])
  return all_paps

def load_and_combine(path_papers):
    all_files = os.listdir(path_papers)
    paths = [os.path.join(path_papers, fl) for fl in all_files]
    paths = [elt for elt in paths if os.path.isfile(elt) and 'encoding' not in elt and 'sqlite' not in elt]  # keep only files

    all_paps = load_gzip(paths[0])
    for p in paths[1:]:
        paps2 = load_gzip(p)
        all_paps.update(paps2)
    return all_paps

def get_root_fname(fname):
  if '_objectives' in fname:
    return fname
  root_fname= '_'.join(fname.split('_')[:-1])+'_objectives'
  return root_fname

def clean_lst(seq):
    ''' remove duplicates from list '''
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

def get_soup(path):
    header = {}
    header[
        'User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    soup = BeautifulSoup(requests.get(path, headers=header, timeout=120).content, 'html.parser')
    return soup

def listdir_time(path):
  files = os.listdir(path)
  paths_files = [os.path.join(path,elt) for elt in files]
  paths_files.sort(key=lambda x: os.path.getmtime(x))
  files_sorted = [elt.split('/')[-1] for elt in paths_files]
  return files_sorted

def remove_from_naimai_dois(dois_to_remove):
    dois = load_gzip(naimai_dois_path)
    print('len before : ', len(dois))
    for doi in dois_to_remove:
        try:
            dois.remove(doi)
        except:
            pass
    print('len after : ', len(dois))
    save_gzip(naimai_dois_path,dois)

def get_keys_to_filter(cnt):
  keys_to_keep = []
  for k in cnt:
     if cnt[k]>1 and k!='O':
       split = k.split('-')
       if len(split)>1:
         keys_to_keep.append(split[1])
     elif cnt[k]>1 and k=='O':
       keys_to_keep.append(k)

  if keys_to_keep:
    pattern = '|'.join(keys_to_keep)
    keys_to_filter = [elt for elt in cnt if not re.findall(pattern,elt)]
    return keys_to_filter
  else:
    return ''

def correct_ner_data(elt):
  text,entities = elt['text'], ast.literal_eval(elt['entities'])
  cnt = Counter(entities)
  keys_to_filter = get_keys_to_filter(cnt)
  if keys_to_filter:
    new_entities = [elt for elt in entities if elt not in keys_to_filter]
    return new_entities
  return entities

def correct_saved_ner_data(ner_df):
    ner_df['entities']=ner_df.apply(correct_ner_data,axis=1)
    return ner_df

def get_doi_by_title(title,crossref,sleep=2):
  try:
    x = crossref.works(query = title, limit = 1)
    doi = x['message']['items'][0]['DOI']
  except:
    doi=''
  time.sleep(sleep)
  return doi

def ssrn_len_docs(path_csvs,idx_start=0,idx_finish=-1):
  csvs = os.listdir(path_csvs)[idx_start:idx_finish]
  paths = [os.path.join(path_csvs,elt) for elt in csvs]
  dfs = [pd.read_csv(elt) for elt in paths]
  csvs_dict = {field: len(df) for field, df in zip(csvs,dfs)}
  return csvs_dict


