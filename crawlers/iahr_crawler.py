import re
from tqdm.notebook import tqdm
from bs4 import BeautifulSoup
import random
import requests
import time

class IAHR_Crawler:
    def __init__(self, field, path,t_min=1,t_max=3):
        self.field = field
        self.path = path
        self.papers_paths = []
        self.total_pages = 999
        self.docs = {'title': [], 'abstract': [], 'authors': [], 'date': [], 'field': [], "keywords":[],"webpage":[]}
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


    def get_abstract(self,body):
        abstract = body[3].text.replace('Abstract: ', '').strip()
        return abstract

    def get_paths_in_page(self, nb_page):
        webpage = self.path +'&page='+nb_page
        soup = self.get_soup(webpage)
        paper_list = soup.find_all(name='tbody')[0]
        papers = paper_list.find_all(name='tr')
        papers_pages = [elt.find(name='a', attrs={'class': 'overflow-text2'})['href'] for elt in papers]
        paths_in_page = ['https://www.iahr.org' + elt for elt in papers_pages]
        return paths_in_page

    def get_papers_pages(self,first_page,last_page):
        for page in tqdm(range(first_page,last_page+1)):
            paths_in_page = self.get_paths_in_page(page)
            self.papers_paths.append(paths_in_page)

    def get_paper_path_content(self,paper_path):
        soup = self.get_soup(paper_path)
        content = soup.find_all(name='div', attrs={'class': 'content-text'})[1]
        return content

    def get_content_body(self,content):
        body = content.find(name='div', attrs={'class': None}).find_all(name='p')
        return body

    def get_keywords(self,body):
        keywords = body[2].text.replace('Keywords: ', '').replace(';',',').strip()
        return keywords

    def get_title(self, content):
        title = content.find(name='h2').text
        return title

    def get_abstract_id(self, description_soup):
        return description_soup.find_all(name="a", attrs={"class": "title optClickTitle"})[0]['href'].split('=')[1]

    def get_date(self, body):
        date = body[5].text.replace('Year: ', '').strip()
        return date

    def get_authors(self, body):
        authors = body[0].text.replace('\nAuthor(s): ','').strip()
        return authors

    def get_docs(self,first_page,last_page):

        #Get articles pages
        print('>> Getting pages..')
        self.get_papers_pages(first_page=first_page,last_page=last_page)
        self.docs = {'title': [], 'abstract': [], 'authors': [], 'date': [], 'field': [], "keywords": [], "webpage": []}

        print('>> Getting papers..')
        #crawl papers
        for path in tqdm(self.papers_paths):
            content = self.get_paper_path_content(path)
            title = self.get_title(content)
            body = self.get_content_body(content)
            abstract = self.get_abstract(body)
            if abstract:
                authors = self.get_authors(body)
                keywords = self.get_keywords(body)
                date = self.get_date(body)

                self.docs['title'].append(title)
                self.docs['abstract'].append(abstract)
                self.docs['authors'].append(authors)
                self.docs['date'].append(date)
                self.docs['field'].append('Environmental Science')
                self.docs['keywords'].append(keywords)
                self.docs['webpage'].append(path)
