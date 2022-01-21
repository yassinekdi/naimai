import re
from tqdm.notebook import tqdm
from bs4 import BeautifulSoup
import random
import requests
import time

def select_span(list_spans):
    for elt in list_spans:
        if 'Posted' in elt.string:
            return elt.string

def find_kwords(soup):
  all_p = soup.find_all(name='p')
  for p in all_p:
    if 'Keywords' in p.getText():
      return p.getText()

class SSRN_Crawler:
    def __init__(self, field, path):
        self.field = field
        self.path = path
        self.soup = {}
        self.total_pages = 999
        self.docs = {'title': [], 'abstract_id': [], 'authors': [], 'date': [], 'field': [], 'nb_page': [],"abstract_box":[], "abstract_text":[],"keywords":[]}

    def get_soup(self, path):
        header = {}
        header[
            'User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
        soup = BeautifulSoup(requests.get(path, headers=header, timeout=10).content, 'html.parser')
        slp=random.randint(3,6)
        time.sleep(slp)
        return soup

    def get_abstract_box(self,id):
        abstract_path = "https://papers.ssrn.com/sol3/papers.cfm?abstract_id="+id
        abstract_soup = self.get_soup(abstract_path)
        abstract_box = abstract_soup.find_all(name="div", attrs={"class": "box-container box-abstract-main"})
        if not abstract_box:
          print('soup :  ',abstract_soup)
          print('problem with abstract id : ', id)
          print('abst box : ', abstract_box)
        return abstract_box[0]

    def get_abstract_text(self,abstract_box):
        return abstract_box.find_all(name='div', attrs={"class": "abstract-text"})[0].find('p').getText()

    def get_page_path(self, nb_page):
        split = self.path.split('cfm?')
        page_path = split[0] + 'cfm?'+ 'npage={}&'.format(nb_page) + split[1]
        return page_path

    def get_all_soups(self):
        self.soup[1] = self.get_soup(self.path)
        self.total_pages = int(self.soup[1].find_all(name="a", attrs={"class": "jeljour_pagination_number"})[-1].string)

        for npage in tqdm(range(2, self.total_pages + 1)):
            path = self.get_page_path(npage)
            self.soup[npage] = self.get_soup(path)

    def get_description_data_npage(self, npage):
        soup = self.soup[npage]
        descriptions = soup.find_all(name="div", attrs={"class": "description"})

        for des in descriptions:
            title = self.get_title(des)
            if title:
                id =  self.get_abstract_id(des)
                if id not in self.docs['abstract_id'] and title not in self.docs['title']:
                  self.docs['title'].append(title)
                  self.docs['abstract_id'].append(id)
                  try:
                      abs_box = self.get_abstract_box(id)
                      self.docs['abstract_box'].append(abs_box)
                  except:
                      print('no abs_box')
                      abs_box=""
                      self.docs['abstract_box'].append(abs_box)

                  if abs_box:
                      try:
                        self.docs['abstract_text'].append(self.get_abstract_text(abs_box))
                      except:
                        self.docs['abstract_text'].append('')
                        print('problem of abstract text in id ', id)
                      try:
                          self.docs['keywords'].append(find_kwords(abs_box))
                      except:
                          self.docs['keywords'].append('')
                  else:
                      self.docs['abstract_text'].append('cd Pych    ')
                      self.docs['keywords'].append('')
                  try:
                      self.docs['authors'].append(self.get_authors(des))
                  except:
                      self.docs['authors'].append('')
                  try:
                      self.docs['date'].append(self.get_date(des))
                  except:
                      self.docs['date'].append('')
                  self.docs['field'].append(self.field)
                  self.docs['nb_page'].append(npage)

    def get_title(self, description_soup):
        title= description_soup.find_all(name="a", attrs={"class": "title optClickTitle"})[0].string
        if not title:
            title = description_soup.find_all(name="a", attrs={"class": "title optClickTitle"})[0].find_all(name="span")[0].string
        return title

    def get_abstract_id(self, description_soup):
        return description_soup.find_all(name="a", attrs={"class": "title optClickTitle"})[0]['href'].split('=')[1]

    def get_date(self, description_soup):
        spans = description_soup.find_all(name="div", attrs={"class": "note note-list"})
        selected_span = [select_span(elt) for elt in spans][0]
        return re.findall('\d+', selected_span)[1]

    def get_authors(self, description_soup):
        authors_elts = description_soup.find_all(name="div", attrs={"class": "authors-list"})
        authors = ''
        for elt in authors_elts:
            authors = ', '.join([elt.string for elt in elt.find_all(name='a')])
        return authors

    def get_docs(self):
        if not self.soup:
            print('Getting soups..')
            self.get_all_soups()
        print('Getting description..')
        for page in tqdm(range(1, self.total_pages + 1)):
            self.get_description_data_npage(page)

