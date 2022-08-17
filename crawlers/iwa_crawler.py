import re
import os
from tqdm.notebook import tqdm
from bs4 import BeautifulSoup
import random
import requests
import time

years_dir = "issue/browse-by-year"
root_dir ="https://iwaponline.com"

class IWA_Crawler:
    def __init__(self, journal_path,t_min=3,t_max=5):
        self.journal_path = journal_path
        self.docs = {'title': [], 'abstract': [], 'authors': [], 'date': [], 'field': [], "keywords":[],"doi":[],"numCitedBy":[]}
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

    def get_years(self):
        path = os.path.join(self.journal_path,years_dir)
        journal_years_soup = self.get_soup(path)
        years_div = journal_years_soup.find_all(name='ol')
        years = [elt.text.replace('\n','').strip() for elt in years_div[0].find_all('li')]
        print(f'From {years[0]} - To {years[-1]} - Total years : {len(years)} ')
        return years

    def get_year_volumes(self,year):
        path = os.path.join(self.journal_path,years_dir,str(year))
        year_soup = self.get_soup(path)
        volumes_divs = year_soup.find_all(name='ol')[0].find_all('li')
        volumes_dirs = [elt.find(name='a')['href'] for elt in volumes_divs]
        return volumes_dirs

    def get_articles_soups_in_volume(self,volume_dir):
        path = root_dir + volume_dir
        soup_issue_articles = self.get_soup(path)
        titles_divs = soup_issue_articles.find_all(name='div', attrs={'class': 'al-article-item-wrap al-normal'})
        articles_href = [elt.find(name='h5').find(name='a')['href'] for elt in titles_divs]
        articles_paths = [root_dir + elt for elt in articles_href]
        print('>> Getting articles soups..')
        articles_soups = [self.get_soup(p) for p in articles_paths]
        return articles_soups

    def get_main_content_article(self,article_soup):
        return article_soup.find(name='div',attrs={'class':'content-inner-wrap'})

    def get_date(self,main_content):
        return main_content.find(name='span',attrs={'class':'article-date'}).text.split()[-1]

    def get_title(self,main_content):
        return main_content.find(name='h1',attrs={'class':'wi-article-title article-title-main'}).text.replace('\r','').replace('\n','').strip()

    def get_authors(self,main_content):
        authors_divs = main_content.find_all(name='a',
                                             attrs={'class': 'linked-name js-linked-name stats-author-info-trigger'})
        authors = ', '.join([elt.text for elt in authors_divs])
        return authors

    def get_doi(self,main_content):
        return main_content.find(name='div', attrs={'class': 'citation-doi'}).text.replace('\n', '').strip()

    def get_abstract(self,main_content):
        abstract= main_content.find(name='section',attrs={'class':'abstract'})
        if abstract:
            return abstract.text
        return ''

    def get_keywords(self,main_content):
        keywords_divs = main_content.find_all(name='a', attrs={'class': 'kwd-part kwd-main'})
        keywords = ', '.join([elt.text for elt in keywords_divs])
        return keywords

    def get_numCitedBy(self,article_soup):
        numCitedBy_div = article_soup.find(name='div', attrs={'class': "article-cited-link-wrap web-of-science"})
        numCitedBy = .5
        if numCitedBy_div:
            numCitedBy_text = numCitedBy_div.text
            numCitedBy = re.findall('\d+', numCitedBy_text)[0]
        return numCitedBy

    def get_volumes_dirs_in_years(self,year1,year2):
        volumes_dirs = [self.get_year_volumes(yr) for yr in tqdm(range(year1,year2+1))]
        print(f'Total volumes : {len(volumes_dirs)}')
        return volumes_dirs

    def get_docs_from_volume(self,volume_dir):
        articles_soups = self.get_articles_soups_in_volume(volume_dir=volume_dir)
        for soup in articles_soups:
            main_content = self.get_main_content_article(soup)
            abstract = self.get_abstract(main_content)
            if abstract:
                title = self.get_title(main_content)
                authors = self.get_authors(main_content)
                date = self.get_date(main_content)
                doi = self.get_doi(main_content)
                keywords = self.get_keywords(main_content)
                numCitedBy = self.get_numCitedBy(soup)

                self.docs['title'].append(title)
                self.docs['abstract'].append(abstract)
                self.docs['authors'].append(authors)
                self.docs['date'].append(date)
                self.docs['field'].append('Environmental Science')
                self.docs['keywords'].append(keywords)
                self.docs['doi'].append(doi)
                self.docs['numCitedBy'].append(numCitedBy)


    def get_docs(self,year1,year2):

        #Get articles pages
        print('>> Getting volumes dirs..')
        volumes_dirs=self.get_volumes_dirs_in_years(year1=year1,year2=year2)
        volumes_dirs = [elt for elt2 in volumes_dirs for elt in elt2]

        print('>> Getting papers..')
        for volume_dir in tqdm(volumes_dirs):
            self.get_docs_from_volume(volume_dir)


