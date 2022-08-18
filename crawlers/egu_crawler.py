import requests
from bs4 import BeautifulSoup
from tqdm.notebook import tqdm
import time
import random

class EGU_Crawler:
    def __init__(self,t_min=2,t_max=4):
        self.docs = {'title': [], 'authors': [], 'date': [], "abstract": [], "doi": [],
                     "field": []}
        self.soups={}
        self.t_min = t_min
        self.t_max = t_max

    def get_soup(self, path,data):
        page = requests.post(path, data=data)
        soup = BeautifulSoup(page.text, 'html.parser')
        slp=random.randint(self.t_min,self.t_max)
        time.sleep(slp)
        return soup

    def get_soups(self,p1,p2,type_):
        data = {
            'rangeMin': 0,
            'rangeMax': 7,
            'manuscriptTypes[]': type_,
        }
        path = 'https://editor.copernicus.org/ms_types.php?journalId=10'
        for page in tqdm(range(p1,p2+1)):
            data['page']=page-1
            self.soups[page]= self.get_soup(path,data)

    def get_title(self,div):
        title_div = div.find(name='a', attrs={'class': 'article-title'})
        titles = title_div.text
        return titles

    def get_date(self,div):
        date_div = div.find(name='div', attrs={'class': 'published-date'})
        date = date_div.text.split()[-1]
        return date

    def get_authors(self,div):
        authors_div = div.find(name='div', attrs={'class': 'authors'})
        authors = authors_div.text
        return authors

    def get_doi(self,div):
        doi_div = div.find(name='div', attrs={'class': 'citation'})
        doi = doi_div.find(name='span').text.replace(',', '').strip()
        return doi

    def get_abstract(self,div):
        abstract_div = div.find(name='div', attrs={'class': 'content'})
        if abstract_div:
            return abstract_div.text.replace('\n', '').strip()
        return ''

    def get_divs(self,soup):
        divs = soup.find_all(name='div', attrs={'class': 'grid-container paperlist-object in-range paperList-final'})
        return divs

    def get_docs(self,p1=1, p2=10,type_=22):
        print('>> Getting soups..')
        self.get_soups(p1=p1,p2=p2,type_=type_)

        print('>> Getting articles..')
        for page in tqdm(self.soups):
            soup = self.soups[page]
            articles_divs=self.get_divs(soup)

            for div in articles_divs:
                abstract = self.get_abstract(div)
                if abstract:
                    title = self.get_title(div)
                    date = self.get_date(div)
                    doi = self.get_doi(div)
                    authors = self.get_authors(div)
                    fields = 'Environmental Science'

                    self.docs['title'].append(title)
                    self.docs['date'].append(date)
                    self.docs['abstract'].append(abstract)
                    self.docs['doi'].append(doi)
                    self.docs['authors'].append(authors)
                    self.docs['field'].append(fields)