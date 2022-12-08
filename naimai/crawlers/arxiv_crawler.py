import dask.bag as db
import json
import subprocess
# from tqdm.notebook import tqdm
from bs4 import BeautifulSoup
import re
from naimai.utils.regex import str_in_list
import os
# import tarfile

class ArXiv_Crawler:
  def __init__(self, arxiv_metadata_dir, tar_dir='',pdfs_dir='', pdf_manifest_dir='',category='',get_manifest=True):
    self.arxiv_metadata_dir = arxiv_metadata_dir
    self.pdf_manifest_dir = pdf_manifest_dir
    self.metadata_dic = {}
    self.all_ids = []
    self.ids_filtered = [] #ids without alphabets
    self.ids_not_found = []
    self.titles=[]
    self.pdfs_dir = pdfs_dir
    self.tar_dir = tar_dir
    self.category = category
    self.no_lettrs_pattern= '^[A-Za-z]'
    self.docs = None

    if get_manifest:
      self.get_metadata_dic_from_manifest()
      self.get_category_ids(self.category, take_all_category_files=True)


  def read(self):
    return db.read_text(self.arxiv_metadata_dir).map(json.loads)

  def get_category_docs(self,take_all_category_files, category):
    all_docs=self.read()
    docs= all_docs.filter(lambda x: x['categories']==category)
    filtered_docs= docs.filter(lambda x: x['comments']!='This paper has been withdrawn')
    if take_all_category_files:
      self.docs = filtered_docs
    else:
      pdf_files = os.listdir(self.pdfs_dir)
      self.docs = filtered_docs.filter(lambda x: x if str_in_list((x['id'] + '.pdf'),
                        pdf_files) else None)
      # self.docs = filtered_docs.filter(lambda x: x if (not str_in_list((x['title']+'_'+x['id']+'.pdf').replace('\n','_').replace('\\','').replace('/',''), pdf_files)) else None)

  def docs2df(self):
    return self.docs.to_dataframe()[['id','authors_parsed','title','abstract','doi']]

  def get_category_ids(self, category, take_all_category_files=True):
    self.get_category_docs(take_all_category_files, category)
    df_category = self.docs2df()
    self.all_ids = list(df_category['id'].apply(lambda x: str(x)))
    # title_list = list(df_category['title'])
    self.ids_filtered = [id for id in self.all_ids if not re.findall(self.no_lettrs_pattern, id)]
    print('  >> IDs = {}  -- IDs filtered = {}'.format(len(self.all_ids), len(self.ids_filtered)))
    # return {'ids': self.ids_filtered, 'titles': title_list}

  def get_metadata_dic_from_manifest(self):
    print('>> Constructing metadata dic')
    with open(self.pdf_manifest_dir, 'r') as manifest:
      soup = BeautifulSoup(manifest, 'xml')
      files = soup.find_all('file')

    for f in files:
      filepath = f.find('filename').text
      self.metadata_dic[filepath] = {'first_item': f.find('first_item').text,
                                'last_item': f.find('last_item').text,
                                'num_items': f.find('num_items').text,
                                'size': int(f.find('size').text) / 1000000000,
                                'yymm': f.find('yymm').text
                                }

  def find_id_tar_in_manifest(self, id_tofind): #id_tofind form : '0704.2668'
    # print('>> Find tar files')
    yymm_tofind = id_tofind.split('.')[0]
    number_tofind = int(id_tofind.split('.')[1])
    potential_paths = [path for path in self.metadata_dic if self.metadata_dic[path]['yymm'] == yymm_tofind]

    potential_paths_filtered = []
    for path in potential_paths:
      dic = self.metadata_dic[path]
      letter_in_items = re.findall(self.no_lettrs_pattern, dic['first_item']) + re.findall(self.no_lettrs_pattern, dic['last_item'])
      if not letter_in_items:
        yymm = dic['yymm']
        first_number = int(dic['first_item'].split('.')[1])
        last_number = int(dic['last_item'].split('.')[1])
        if number_tofind in range(first_number, last_number):
          tar_name = '_'.join([yymm, str(first_number), str(last_number)]) + '.tar'  # yymm_start_finish
          potential_paths_filtered.append({'path': path,
                                         'filename': tar_name})
    return potential_paths_filtered

  def download_tar(self, pdf_s3_path,output_path,output_filename):
    # print('>> tar download : ')
    output = os.path.join(output_path, output_filename)
    if output_filename not in os.listdir(output_path):
      cmd = 's3cmd get --recursive --requester-pays --skip-existing s3://arxiv/{} {}'.format(pdf_s3_path, output)
      subprocess.call(cmd,shell=True)

  def id_in_tar_dir(self,id):
    potential_paths_filtered = self.find_id_tar_in_manifest(id)
    if len(potential_paths_filtered) > 0:
      output_filename = potential_paths_filtered[0]['filename']
      if output_filename in os.listdir(self.tar_dir):
        return True
    return False

  def ids_in_tar_dir(self):
    result = {'ids found': [], 'ids not found': []}
    for id in self.ids_filtered:
      if self.id_in_tar_dir(id):
        result['ids found'].append(id)
      else:
        result['ids not found'].append(id)
    return result



  def download_tar_files(self):

    for id in self.ids_filtered:
      potential_paths_filtered = self.find_id_tar_in_manifest(id)
      if len(potential_paths_filtered)>0:
        pdf_s3_path = potential_paths_filtered[0]['path']
        output_path = self.tar_dir
        output_filename = potential_paths_filtered[0]['filename']
        self.download_tar(pdf_s3_path,output_path, output_filename)
        if len(potential_paths_filtered)>1:
          print('  >> LEN >1 FOR ID ', id)
      else:
        self.ids_not_found.append(id)
        print('  >> PROBLEM WITH ID ', id)


  # def download_lost_ids(self):
  #   useragent = UserAgent()
  #   for id in tqdm(self.ids_not_found):
  #     url = 'https://arxiv.org/pdf/'+str(id)
  #     ua = useragent.random
  #     response = requests.get(url, headers={'User-Agent': ua})
  #     with open(self.pdfs_dir, 'wb') as f:
  #       f.write(response.content)
  #     time.sleep(np.random.random() + 5)

  def tar2pdfs(self):
    for id in self.ids_filtered:
      self.get_id_file_from_tars(id)

  def get_id_file_from_tars(self,id):
    tar_files_dic = [{'yymm': elt.split('_')[0],
                      'first_item': elt.split('_')[1],
                      'last_item': elt.split('_')[2].replace('.tar', ''), }
                     for elt in os.listdir(self.tar_dir)]
    id_dic = {'yymm': id.split('.')[0], 'number': id.split('.')[1]}
    mytar=''
    for tar in tar_files_dic:
      if id_dic['yymm'] == tar['yymm']:
        if int(id_dic['number']) in range(int(tar['first_item']), int(tar['last_item'])):
          mytar = tar['yymm'] + '_' + tar['first_item'] + '_' + tar['last_item'] + '.tar'
          break

    # try:
    #   if mytar:
    #     tarfile_dir = os.path.join(self.tar_dir, mytar)
    #     tar = tarfile.open(tarfile_dir)
    #     tar_content = tar.getnames()
    #     id_in_tar = [elt for elt in tar_content if id in elt]
    #
    #     if id_in_tar:
    #       id_in_tar = id_in_tar[0]
    #       if id_in_tar not in self.pdfs_dir:
    #         tar.extract(id_in_tar, self.pdfs_dir)
    # except:
    #   print('problem in id : {}, mytar : {} '.format(id,mytar))


  def clean_dir(self):
    folders_path = [os.path.join(self.pdfs_dir, fold).replace(' ', '\\ ') for fold in os.listdir(self.pdfs_dir)]
    for fold in folders_path:
      os.system('mv {}/* {}'.format(fold, self.pdfs_dir.replace(' ', '\\ ')))
      os.system('rm -r {}'.format(fold))
