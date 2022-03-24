import pickle, gzip, pickletools
import requests
from bs4 import BeautifulSoup
import os
from naimai.constants.paths import naimai_dois_path
import ast
from collections import Counter
import re

def load_gzip(path):
    with gzip.open(path, 'rb') as f:
        p = pickle.Unpickler(f)
        return p.load()

def save_gzip(path,obj):
    with gzip.open(path, "wb") as f:
        pickled = pickle.dumps(obj)
        optimized_pickle = pickletools.optimize(pickled)
        f.write(optimized_pickle)

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