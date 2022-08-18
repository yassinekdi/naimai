import requests
from bs4 import BeautifulSoup
from tqdm.notebook import tqdm
import time
import random

class EGU_crawler:
    def __init__(self,t_min=1,t_max=3):
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

    def get_soups(self,p1,p2):
        data = {
            'rangeMin': 0,
            'rangeMax': 7,
            'manuscriptTypes[]': 22,
            'manuscriptTypes[]': 23,
            'manuscriptTypes[]': 218,
            'manuscriptTypes[]': 235,
            'manuscriptTypes[]': 199,
            'manuscriptTypes[]': 251,
        }
        path = 'https://editor.copernicus.org/ms_types.php?journalId=10'
        for page in range(p1,p2+1):
            data['page']=page-1
            self.soups[page]= self.get_soup(path,data)

    def get_titles(self,soup):
        titles_divs = soup.find_all(name='a', attrs={'class': 'article-title'})
        titles = [elt.text for elt in titles_divs]
        return titles

    def get_dates(self,soup):
        dates_divs = soup.find_all(name='div', attrs={'class': 'published-date'})
        dates = [elt.text.split()[-1] for elt in dates_divs]
        return dates

    def get_authors(self,soup):
        authors_divs = soup.find_all(name='div', attrs={'class': 'authors'})
        authors = [elt.text for elt in authors_divs]
        return authors

    def get_dois(self,soup):
        dois_div = soup.find_all(name='div', attrs={'class': 'citation'})
        dois = [elt.find(name='span').text.replace(',', '').strip() for elt in dois_div]
        return dois

    def get_abstracts(self,soup):
        abstracts_divs = soup.find_all(name='div', attrs={'class': 'content'})
        abstracts = [elt.text.replace('\n', '').strip() for elt in abstracts_divs]
        return abstracts

    def get_docs(self,p1=1, p2=10):
        self.get_soups(p1=p1,p2=p2)

        for page in tqdm(self.soups):
            soup = self.soups[page]
            titles = self.get_titles(soup)
            dates = self.get_dates(soup)
            abstracts = self.get_abstracts(soup)
            dois = self.get_dois(soup)
            authors = self.get_authors(soup)
            fields = ['Environmental Science']*len(abstracts)

            self.docs['title']+=titles
            self.docs['dates'] += dates
            self.docs['abstracts'] += abstracts
            self.docs['dois'] += dois
            self.docs['authors'] += authors
            self.docs['fields'] += fields
