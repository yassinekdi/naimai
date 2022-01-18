import re
from tqdm.notebook import tqdm
from bs4 import BeautifulSoup
import requests

def select_span(list_spans):
    for elt in list_spans:
        if 'Posted' in elt.string:
            return elt.string


class SSRN_Crawler:
    def __init__(self, field, path):
        self.field = field
        self.path = path
        self.soup = {}
        self.total_pages = 999
        self.docs = {'title': [], 'abstract_id': [], 'authors': [], 'date': [], 'field': [], 'nb_page': []}

    def get_soup(self, path):
        header = {}
        header[
            'User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
        soup = BeautifulSoup(requests.get(path, headers=header, timeout=10).content, 'html.parser')
        return soup

    def get_page_path(self, nb_page):
        split = self.path.split('cfm?')
        page_path = split[0] + 'npage={}&'.format(nb_page) + split[1]
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
                self.docs['title'].append(title)
                self.docs['abstract_id'].append(self.get_abstract_id(des))
                self.docs['authors'].append(self.get_authors(des))
                self.docs['date'].append(self.get_date(des))
                self.docs['field'].append(self.field)
                self.docs['nb_page'].append(npage)

    def get_title(self, description_soup):
        return description_soup.find_all(name="a", attrs={"class": "title optClickTitle"})[0].string

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
        # if not self.soup:
        #   self.get_all_soups()
        for page in range(1, self.total_pages + 1):
            page_data = self.get_description_data_npage(page)

