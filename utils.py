from io import StringIO, BytesIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from .constants.regex import regex_doi, regex_etal_and, regex_remove_nbs_from_end, regex_capital, regex_words_authors, regex_words_in_brackets
from .constants.nlp import this_year
from .constants.paths import Mybucket
import requests
import numpy as np
import time
from collections import OrderedDict
import unidecode
from bs4 import BeautifulSoup
import re
from sys import platform
import pdf2image
import pytesseract
import pickle, gzip

# def generate_url(client,fname):
#     url = client.generate_presigned_url('get_object', Params={'Bucket': Mybucket,
#                                                               "Key": fname})
#     return url.split('?')[0]

# def upload_files(client,file_,dir,filename):
#     client.put_object(Body=file_ ,Bucket =Mybucket, Key=dir+'/'+filename)
    # client.upload_file(Filename=dir + '/'+filename, Bucket="naimabucket", Key="Data Analysis/" + pdf_file)

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

        pap.Conclusion = multiple_replace(abbreviations_dict, pap.Conclusion)
        pap.Conclusion = correct_abbrevs_replacement(pap.Conclusion)

        pap.Keywords = multiple_replace(abbreviations_dict, pap.Keywords)
        pap.Keywords = correct_abbrevs_replacement(pap.Keywords)
    return pap

def find_root_verb(sentence):
    root_token = None
    for token in sentence:
        if (token.dep_ == 'ROOT') and (token.pos_ == 'VERB'):
            root_token = token
            break
    return root_token

def path_in_os(path):
    if '\\' in path:
        sep = '\\'
    elif '/' in path:
        sep = '/'
    split = path.split(sep)

    if 'win' in platform:
        return r'' + '\\'.join(split)
    elif 'linux' in platform:
        return '/'.join(split)

def score_sentence(sentence,intro):
  # suppose that sentence.split contains at most 2 elts
  split = sentence.split()
  score=0
  if len(split)==2:
    if split[0] in intro:
      score+=1/len(split)
    if split[1] in intro:
      score+=1/len(split)
  else:
    if split[0] in intro:
      score+=1
  return score

def multiple_replace(dictt, text):
    # Create a regular expression  from the dictionary keys
    regex = re.compile("(%s)" % "|".join(map(re.escape, dictt.keys())))

    # For each match, look-up corresponding value in dictionary
    return regex.sub(lambda mo: dictt[mo.string[mo.start():mo.end()]], text)


def convert_pdf_to_txt(obj,is_path=True,use_ocr=False):
    result = ''
    try:
        result=pm_convert_pdf_to_txt(obj,is_path=is_path)
        nb_new_lines = len(re.findall('\n[^.?]\n', result))
        if (nb_new_lines >5000) or nb_new_lines==0:
            result = ''
            if is_path:
                print('OCR TO USE in ', obj)
            else:
                print('OCR USED')
            if use_ocr:
                result = ocr_convert_pdf_to_txt(obj,is_path=is_path)

    except:
        if is_path:
            print('except OCR USED in ', obj)
        else:
            print('OCR USED')
        if use_ocr:
            result = ocr_convert_pdf_to_txt(obj,is_path=is_path)

    return result

def ocr_convert_pdf_to_txt(obj,is_path=True):
    if is_path:
        with open(obj, 'rb') as f:
            pdf_content = f.read()
    else:
        pdf_content = BytesIO(obj)

    doc = pdf2image.convert_from_bytes(pdf_content)
    article = []
    for page_data in doc:
        txt = pytesseract.image_to_string(page_data).encode("utf-8")
        article.append(txt.decode("utf-8"))
    text = " ".join(article)
    return unidecode.unidecode(text.replace('e´', 'é'))

def pm_convert_pdf_to_txt(obj, pages=None,is_path=True):
    if not pages:
        pagenums = set()
    else:
        pagenums = set(pages)
    output = StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)

    if is_path:
        infile = open(obj, 'rb')
    else:
        infile = BytesIO(obj)
    for page in PDFPage.get_pages(infile, pagenums):
        interpreter.process_page(page)
    infile.close()
    converter.close()
    text = output.getvalue()
    output.close()
    return unidecode.unidecode(text.replace('e´','é'))

def find_in_txt(original,lower_txt):
  idx1=original.lower().find(lower_txt)
  idxN = idx1 + len(lower_txt)
  return original[idx1:idxN]

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

def str1_str2_from_txt(str1,str2,txt):
  pattern=str1+'(.*?)'+str2
  srch= re.search(pattern,txt, flags=re.S)
  return srch.group(1)

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

def get_soup(path):
    source = requests.get(path)
    soup = BeautifulSoup(source.text, 'html.parser')
    time.sleep(np.random.random()+2)
    return soup

def doi_from_path(path):
    doi_in_path = doi_in_text(path)
    if doi_in_path:
        return doi_in_path

    soup = get_soup(path)
    if 'doi' in soup.text.lower():
        doi = doi_in_text(soup.text)
        return doi
    return

def doi_from_urls(reference,urls,error_file_name):
    doi=0
    for url in urls:
        if '.pdf' in url:
            write_error_func(file_path=error_file_name,
                             error='-----  PDF TO DOWNLOAD FOR for {} ----- \n  URL : {} \n\n'.format(reference, url))
        try:
            doi = doi_from_path(url)
        except:
            pass
        if doi:
            doi = re.sub(regex_remove_nbs_from_end, '', doi)
            break
    return doi

def reinsert_commas(with_comma,without_comma):
  split = with_comma.split(',')
  if (len(split)==3) and ',' not in without_comma:
    split=split[1]
    return without_comma.replace(split,','+split+',')
  else:
    return without_comma

def write_error_func(file_path, error):
    with open(file_path, 'a') as f:
        f.write(error)

def verify_citation(citation):
    search = re.search(regex_etal_and, citation)
    length = len(citation.split()) > 1 and len(citation.split()) < 6
    if search and length:
        return True
    return False

def get_duplicates(text,threshold):
    capital_sentences =  re.split(regex_capital,text)[1:]
    duplicate = [(elt,capital_sentences.count(elt)) for elt in capital_sentences if capital_sentences.count(elt)>threshold and len(elt.split())>1]
    duplicate.sort(key=lambda x: x[1])
    set_duplicate = set(duplicate[::-1])
    return [elt[0] for elt in set_duplicate]

def clean_ref(ref):
  split=re.split(r'[\.,\(\)]',ref)
  split.sort(key=lambda x: len(x))
  return split[-1]

def title_in_file_name(filename,title):
  title_split = title.split()
  words_in_filename = [elt in filename for elt in title_split]
  if sum(words_in_filename)>0.7*len(words_in_filename):
      return True
  return False
  # return all(elt in filename for elt in title_split)

def find_references(ref,file_names):
  title=clean_ref(ref)
  right_file = [fname for fname in file_names if title_in_file_name(fname,title)]
  return right_file


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

def optimize_all_papers(all_paps):
  all_paps_opt = {}
  all_paps_opt['pdfs_dir'] = all_paps['pdfs_dir']

  all_paps_opt['elements'] = {}
  for elt in all_paps['elements']:
    all_paps_opt['elements'][elt] = {}
    all_paps_opt['elements'][elt]['file_name'] = all_paps['elements'][elt]['file_name']
    all_paps_opt['elements'][elt]['Authors'] = all_paps['elements'][elt]['Authors']
    all_paps_opt['elements'][elt]['Publication_year'] = all_paps['elements'][elt]['Publication_year']
    all_paps_opt['elements'][elt]['Objective_sentences'] = all_paps['elements'][elt]['Objective_sentences']
    all_paps_opt['elements'][elt]['Objective_paper'] = all_paps['elements'][elt]['Objective_paper']
  return all_paps_opt

def year_from_arxiv_fname(fname):
  yy = fname.split('.')[0][:2]
  if int('20'+yy)>this_year:
    yy = '19'+yy
  else:
    yy = '20'+yy
  return yy

def load_gzip(path):
    with gzip.open(path, 'rb') as f:
        p = pickle.Unpickler(f)
        return p.load()