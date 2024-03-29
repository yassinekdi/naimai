from tqdm.notebook import tqdm
import os
from bs4 import BeautifulSoup
import random
import requests
import time

class Scholar_Crawler:
    def __init__(self, person,field, path,t_min=3,t_max=5):
        self.field = field
        self.person = person
        self.path = path
        self.soup = self.get_local_soup(path)
        self.docs = {'title': [], 'abstract': [], 'authors': [], 'date': [], 'field': [],'website':[], 'numCitedBy': [],'journal': []}
        self.t_min=t_min
        self.t_max=t_max

    def get_soup(self, path):
        header = {}
        header[
            'User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
        soup = BeautifulSoup(requests.get(path, headers=header, timeout=15).content, 'html.parser')
        slp=random.randint(self.t_min,self.t_max)
        time.sleep(slp)
        return soup

    def get_local_soup(self,path):
        with open(path) as fp:
            soup = BeautifulSoup(fp, 'html.parser')
        return soup

    def get_abstract_text(self,abstract_box):
        return abstract_box.find_all(name='div', attrs={"class": "abstract-text"})[0].find('p').getText()

    def get_years(self):
        return [elt.text for elt in self.soup.find_all(name='span', attrs={'class': 'gsc_a_h gsc_a_hc gs_ibl'})]

    def get_titles_elts(self):
        return self.soup.find_all(name='a', attrs={'class': 'gsc_a_at'})

    def get_articles_pages(self,titles_elts):
        return [elt['href'] for elt in titles_elts]

    def get_titles(self, titles_elts):
        return [elt.text for elt in titles_elts]

    def get_numCitedBy(self):
        return [elt.text for elt in self.soup.find_all(name='a', attrs={'class': 'gsc_a_ac gs_ibl'})]

    def get_article_page(self, website, dir_file, title,idx_start,idx):
        title = title + '.html'
        path_file = os.path.join(dir_file, title)

        if idx<idx_start:
            soup = self.get_local_soup(path_file)
        else:
            soup = self.get_soup(website)

        with open(path_file, "w") as file:
            file.write(str(soup))
        return path_file

    def get_article_metadata(self,soup):
        return soup.find_all(name='div', attrs={'class': 'gsc_oci_value'})

    def get_abstract(self,soup):
        abstract =soup.find_all(name='div', attrs={'class': 'gsh_csp'})
        if abstract:
            return abstract[0].text
        else:
            return ''

    def get_docs(self,idx_start=0):
        print('>> Local data..')
        titles_elts= self.get_titles_elts()
        self.docs['website'] = self.get_articles_pages(titles_elts)
        self.docs['title'] = self.get_titles(titles_elts)
        self.docs['numCitedBy'] = self.get_numCitedBy()
        self.docs['date'] = self.get_years()

        print('>> Download articles pages')
        if not os.path.exists(self.person):
            os.mkdir(self.person)
        file_dir = self.person
        websites,titles = self.docs['website'], self.docs['title']
        idx=0
        for website,title in tqdm(zip(websites,titles),total=len(websites)):
            try:
                path_file= self.get_article_page(website,file_dir,title,idx_start,idx)
                soup_article = self.get_local_soup(path_file)
                meta_data = self.get_article_metadata(soup_article)
                self.docs['authors'].append(meta_data[0].text)
                self.docs['journal'].append(meta_data[2].text)
                self.docs['abstract'].append(self.get_abstract(soup_article))
            except:
                print('problem in title', title)
                self.docs['authors'].append('')
                self.docs['journal'].append('')
                self.docs['abstract'].append('')

            idx+=1
        self.docs['field']= [self.field]*len(websites)
        print('>> Done !')




