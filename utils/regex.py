import re
from naimai.constants.regex import regex_doi, regex_words_authors, regex_words_in_brackets, regex_capital, regex_in_brackets
from naimai.constants.nlp import this_year
from naimai.constants.paths import aws_root_pdfs,doi_url,arxiv_pdfs_url
from collections import OrderedDict
import os

def get_nb_words(text):
    split = text.split()
    return len(split)


def multiple_replace(dictt, text):
    # Create a regular expression  from the dictionary keys
    regex = re.compile("(%s)" % "|".join(map(re.escape, dictt.keys())))

    # For each match, look-up corresponding value in dictionary
    return regex.sub(lambda mo: dictt[mo.string[mo.start():mo.end()]], text)

def reinsert_commas(with_comma,without_comma):
  split = with_comma.split(',')
  if (len(split)==3) and ',' not in without_comma:
    split=split[1]
    return without_comma.replace(split,','+split+',')
  else:
    return without_comma

def transform_field_name(field_name):
    dic_replace = {
        ' ': '%20',
        '(': '%28',
        ')': '%29'
    }
    return multiple_replace(dic_replace, field_name)

def str1_str2_from_txt(str1,str2,txt):
  pattern=str1+'(.*?)'+str2
  srch= re.search(pattern,txt, flags=re.S)
  return srch.group(1)


def correct_abbrevs_replacement(parag):
  wrds_btween_brakets = re.findall(regex_words_in_brackets,parag)
  words_repeated = [words for words in wrds_btween_brakets if len(parag.split(words))>2]
  for words in words_repeated:
    parag = re.sub(' \('+words+'\)', '',parag)
  return parag

def replace_abbreviations(pap):
    abbreviations_dict = pap.get_abbreviations_dict()
    if abbreviations_dict:
        pap.Abstract = multiple_replace(abbreviations_dict, pap.Abstract)
        pap.Abstract = correct_abbrevs_replacement(pap.Abstract)
        # pap.Conclusion = multiple_replace(abbreviations_dict, pap.Conclusion)
        # pap.Conclusion = correct_abbrevs_replacement(pap.Conclusion)

        pap.Keywords = multiple_replace(abbreviations_dict, pap.Keywords)
    return pap

def hasNumbers(inputString):
  return bool(re.search(r'\d', inputString))


def get_pattern(txt):
  pattern = r'^[\n\d\s]+\w+.*'
  patn = re.compile(pattern,flags= re.M | re.I)
  lst=re.findall(patn,txt)
  for elt in lst:
    if 'introduction' in elt.lower():
      if hasNumbers(elt):
        if '.' in elt:
          pattern = r'^\d\.[\n\s]+[a-zA-Z]+.*'
          return pattern
        else:
          pattern = r'^\d[\n\s]+[a-zA-Z]+.*'
          return pattern
  return

def starts_with_capital(text):
  regex= r'^\s*?[A-Z].*'
  result=re.findall(regex,text)
  if result:
    return True
  return False

def doi_in_text(text):
    reg = re.compile(regex_doi, re.VERBOSE + re.IGNORECASE)
    result = re.findall(reg, text)
    if result:
        try:
            return [elt for elt in result[0] if (len(elt) > 5) and ('http' not in elt)][0]
        except:
            pass
    return ''

def clean_objective_stc(stc):
  stc2=stc.replace(';', ',')
  stc3= re.sub('\(\d+\)', '', stc2)
  stc4= re.sub('\[\d+\]', 'Someone', stc3)
  stc5= re.sub('^\d+','',stc4)
  return stc5.replace('- ', '')

def clean_objectives(split):
  split_cln1 = [clean_objective_stc(stc) for stc in split]
  split_cln2= [re.sub('^\s+|\s+$','',elt) for elt in split_cln1]
  split_cln3= [re.sub('\s+',' ',elt) for elt in split_cln2 if elt]
  return split_cln3

def clean_authors_stc(stc):
  stc2=stc.replace('\n', '; ').replace("&", ',').replace('.', '. ')
  stc2 = re.sub(regex_words_authors,' ', stc2)
  return stc2

def clean_authors(split):
  split_cln1 = [clean_authors_stc(stc) for stc in split]
  split_cln2= [re.sub('^\s+|\s+$','',elt) for elt in split_cln1]
  split_cln3= [re.sub('\s+',' ',elt) for elt in split_cln2]
  return split_cln3

def check_author(author):
    split = author.split()
    if len(split)>1:
        if len(split[0])>1 and len(split[1])>1:
            return True
    return False

def fix_duplicate_authors(authors_list):
    remove_duplicates=list(set([elt.lower() for elt in authors_list]))
    capitalize_authors = [capitalize(txt) for txt in remove_duplicates]
    if authors_list:
        idx_1st_author = capitalize_authors.index(authors_list[0])
        if idx_1st_author!=0:
            new_list=[authors_list[0]]+[elt for elt in capitalize_authors if elt!=authors_list[0]]
            return new_list
        else:
            return capitalize_authors
    return

def capitalize(text):
  def cap(match):
    return (match.group().capitalize())
  pat = re.compile(r'\w+')
  return pat.sub(cap, text)

def str_in_list(str_,lst):
  found=[elt for elt in lst if str_ in elt]
  if found:
    return True
  return False

def authors_with_commas(authors_str):
    commas_split = authors_str.split(',')
    first_author = commas_split[0].split()[-1]

    if len(commas_split) > 2:
        return first_author + ' et al.'

    second = commas_split[1]

    if second:
        if len(second.split()) > 2:
            return first_author + ' et al.'

        second_author = second.split()[-1]
        return first_author + ' and ' + second_author


def authors_with_period(authors_str):
    period_split = authors_str.split('.')
    if len(period_split) == 2:
        first_author = period_split[-1]
        return re.sub(r'^\s+|\s+$', '', first_author)

    regex_authors = r'^[A-Z]\.(.*?)[A-Z]\.'
    first_author = re.findall(regex_authors, authors_str)[0]
    first_author = re.sub(r'^\s+|\s+$', '', first_author)

    split = authors_str.split(first_author)
    return authors_with_commas(split[0] + first_author + ', ' + split[1])


def authors_with_full_name(authors_str):
    if len(authors_str.split()) % 2 == 0:
        auths_split = authors_str.split()
        new_authors_list = list(
            OrderedDict.fromkeys([' '.join(auths_split[idx:idx + 2]) for idx in range(0, len(auths_split), 2)]))
        return authors_with_commas(', '.join(new_authors_list))

    return

def year_from_arxiv_fname(fname):
  yy = fname.split('.')[0][:2]
  if int('20'+yy)>this_year:
    yy = '19'+yy
  else:
    yy = '20'+yy
  return yy

def find_root_verb(sentence):
    root_token = None
    for token in sentence:
        if (token.dep_ == 'ROOT') and (token.pos_ == 'VERB'):
            root_token = token
            break
    return root_token

def filter_min_length(lst, min_len=2):
    new_list = []
    for elt in lst:
        words = re.findall(r'[a-zA-Z]+', elt)
        idx = 0
        for word in words:
            if len(word) <= min_len:
                idx += 1
        if idx < len(words):
            new_list.append(elt)
    return new_list

def get_duplicates(text,threshold):
    capital_sentences =  re.split(regex_capital,text)[1:]
    duplicate = [(elt,capital_sentences.count(elt)) for elt in capital_sentences if capital_sentences.count(elt)>threshold and len(elt.split())>1]
    duplicate.sort(key=lambda x: x[1])
    set_duplicate = set(duplicate[::-1])
    return [elt[0] for elt in set_duplicate]

def tokenId_in_txt(token,text,last_tokenId=0):
  # find token index in word level in text
  tokens = text.split()
  list_ids = [idx for idx,tok in enumerate(tokens) if tok==token and idx>=last_tokenId]
  return list_ids


def get_first_last_token_ids(sentence, text,last_tokenId=0):
    first_token = sentence.split()[0]

    first_token_id = tokenId_in_txt(first_token, text,last_tokenId=last_tokenId)
    # if len(first_token_id) > 1:
        # print(f'PROBLEM: many first token ids: {first_token_id}')
    first_token_id = first_token_id[0]

    last_token_id = first_token_id + len(sentence.split()) - 1

    return range(first_token_id, last_token_id)

def remove_between_brackets(text,nb_words=5):
  txt_in_brackets = re.findall(regex_in_brackets,text)
  txt_to_remove=[]
  if txt_in_brackets:
    for txt in txt_in_brackets:
      nb_words_txt = len(txt.split())
      if nb_words_txt>nb_words:
        rgx = re.escape('('+txt+')')
        txt_to_remove.append(rgx)

  regex_remove = '|'.join(txt_to_remove)
  return re.sub(regex_remove,'',text)

def get_ref_url(paper,doi=''):
    database = paper['database']
    if database == "mine":
        title = paper['Title']
        fname=''
        if title:
            fname = title+'.pdf'
          # fname = title.replace('/','_char_')[:100].replace("'",'_')+'.pdf'

        url = os.path.join(aws_root_pdfs, 'Geophysics', transform_field_name(fname))
        return url
    if database == "arxiv":
        url = arxiv_pdfs_url + paper['doi']
        return url
    if database =="iahr":
        url =paper['doi']
        return url
    else:
        if not doi:
            doi = paper['doi']
        url = doi_url + doi
        return url
