

from .constants.paths import Mybucket
import requests
import numpy as np
import time


from bs4 import BeautifulSoup

from sys import platform



# def generate_url(client,fname):
#     url = client.generate_presigned_url('get_object', Params={'Bucket': Mybucket,
#                                                               "Key": fname})
#     return url.split('?')[0]

# def upload_files(client,file_,dir,filename):
#     client.put_object(Body=file_ ,Bucket =Mybucket, Key=dir+'/'+filename)
    # client.upload_file(Filename=dir + '/'+filename, Bucket="naimabucket", Key="Data Analysis/" + pdf_file)








# def path_in_os(path):
#     if '\\' in path:
#         sep = '\\'
#     elif '/' in path:
#         sep = '/'
#     split = path.split(sep)
#
#     if 'win' in platform:
#         return r'' + '\\'.join(split)
#     elif 'linux' in platform:
#         return '/'.join(split)

# def score_sentence(sentence,intro):
#   # suppose that sentence.split contains at most 2 elts
#   split = sentence.split()
#   score=0
#   if len(split)==2:
#     if split[0] in intro:
#       score+=1/len(split)
#     if split[1] in intro:
#       score+=1/len(split)
#   else:
#     if split[0] in intro:
#       score+=1
#   return score










# def get_soup(path):
#     source = requests.get(path)
#     soup = BeautifulSoup(source.text, 'html.parser')
#     time.sleep(np.random.random()+2)
#     return soup

# def doi_from_path(path):
#     doi_in_path = doi_in_text(path)
#     if doi_in_path:
#         return doi_in_path
#
#     soup = get_soup(path)
#     if 'doi' in soup.text.lower():
#         doi = doi_in_text(soup.text)
#         return doi
#     return

# def doi_from_urls(reference,urls,error_file_name):
#     doi=0
#     for url in urls:
#         if '.pdf' in url:
#             write_error_func(file_path=error_file_name,
#                              error='-----  PDF TO DOWNLOAD FOR for {} ----- \n  URL : {} \n\n'.format(reference, url))
#         try:
#             doi = doi_from_path(url)
#         except:
#             pass
#         if doi:
#             doi = re.sub(regex_remove_nbs_from_end, '', doi)
#             break
#     return doi



# def write_error_func(file_path, error):
#     with open(file_path, 'a') as f:
#         f.write(error)

# def verify_citation(citation):
#     search = re.search(regex_etal_and, citation)
#     length = len(citation.split()) > 1 and len(citation.split()) < 6
#     if search and length:
#         return True
#     return False



# def clean_ref(ref):
#   split=re.split(r'[\.,\(\)]',ref)
#   split.sort(key=lambda x: len(x))
#   return split[-1]
#
# def title_in_file_name(filename,title):
#   title_split = title.split()
#   words_in_filename = [elt in filename for elt in title_split]
#   if sum(words_in_filename)>0.7*len(words_in_filename):
#       return True
#   return False
#   # return all(elt in filename for elt in title_split)
#
# def find_references(ref,file_names):
#   title=clean_ref(ref)
#   right_file = [fname for fname in file_names if title_in_file_name(fname,title)]
#   return right_file







# def optimize_all_papers(all_paps):
#   all_paps_opt = {}
#   all_paps_opt['pdfs_dir'] = all_paps['pdfs_dir']
#
#   all_paps_opt['elements'] = {}
#   for elt in all_paps['elements']:
#     all_paps_opt['elements'][elt] = {}
#     all_paps_opt['elements'][elt]['file_name'] = all_paps['elements'][elt]['file_name']
#     all_paps_opt['elements'][elt]['Authors'] = all_paps['elements'][elt]['Authors']
#     all_paps_opt['elements'][elt]['Publication_year'] = all_paps['elements'][elt]['Publication_year']
#     all_paps_opt['elements'][elt]['Objective_sentences'] = all_paps['elements'][elt]['Objective_sentences']
#     all_paps_opt['elements'][elt]['Objective_paper'] = all_paps['elements'][elt]['Objective_paper']
#   return all_paps_opt



