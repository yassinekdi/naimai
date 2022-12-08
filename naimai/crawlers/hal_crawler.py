import re
from tqdm.notebook import tqdm
from bs4 import BeautifulSoup
import random
import requests
import time
from naimai.constants.regex import regex_paper_year


class HAL_crawler:
    def __init__(self, path, hal_field, t_min=1, t_max=4):
        # path= 'https://hal.archives-ouvertes.fr/search/index/?q=%2A&sort=submittedDate_tdate+desc&docType_s=ART&language_s=en&level0_domain_s=sde&page=XXX'
        self.path = path
        self.soup = {}
        self.hal_field = hal_field
        self.docs = {'title': [], 'authors': [], 'date': [], 'fields': [], "abstract": [], 'keywords': [], "doi": [],
                     'journal': [], 'hal_address': []}
        self.t_min = t_min
        self.t_max = t_max
        self.divs = []

    def get_soup(self, path, timeit):
        header = {}
        header[
            'User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
        soup = BeautifulSoup(requests.get(path, headers=header, timeout=60).content, 'html.parser')
        slp = random.randint(self.t_min, self.t_max)
        if timeit:
            time.sleep(slp)
        return soup

    def get_divs_page(self, soup_page):
        divs = soup_page.find_all('div')
        divs_filtered = [elt for elt in divs if elt.find_all(name='span', attrs={
            'class': "ref-authors"})]  # remove other divs than those of articles
        divs_filtered2 = [elt for elt in divs_filtered if
                          len(elt.find_all(name='strong')) == 1]  # remove some divs that gather all articles
        return divs_filtered2

    def get_dois_page_and_divs_filtered(self, divs_filtered):
        dois = []
        divs_filtered3 = []
        for elt in divs_filtered:
            doi = elt.find(name='a', attrs={'target': '_blank'})
            if doi:
                doi = doi.text.replace('⟨', '').replace('⟩', '')
                if doi not in dois:
                    dois.append(doi)
                    divs_filtered3.append(elt)
        return (dois, divs_filtered3)

    def get_titles_page(self, divs_filtered):
        titles = [elt.find('strong').text for elt in divs_filtered]
        return titles

    def get_authors(self,divs_filtered):
        authors = [elt.find(name='span', attrs={'class': "ref-authors"}).text.replace('\xa0',' ') for elt in divs_filtered]
        return authors

    def get_hal_addresses_page(self, divs_filtered):
        hal_addresses = [elt.find(name='a', attrs={'class': 'ref-halid'}).text for elt in divs_filtered]
        return hal_addresses

    def get_journals_page(self, soup_article):
        # journals = []
        div = soup_article.find('div', attrs={'class': "widget-content ref-biblio"})
        if div.find('i'):
            return div.find('i').text
        return ''
        # for elt in divs_filtered:
        #     for journal in elt.find_all('i'):
        #         if journal.text != 'et al.':
        #             journals.append(journal.text)
        #
        # return journals

    def get_years_pages(self, divs_filtered,dois):
        dates = []
        for idx, elt in enumerate(divs_filtered):
            doi = dois[idx]
            all_txt = elt.find_all('br')[1].text.replace(doi, '')

            year = re.findall(regex_paper_year, all_txt)
            if year:
                year = year[0]
            elif not year and 'In press' in all_txt:
                year = '2022'
            else:
                year = ''
            dates.append(year)
        return dates

    def get_soup_article(self, hal_address,doi):
        path_article = 'https://hal.archives-ouvertes.fr/' + hal_address
        try:
            soup_article = self.get_soup(path_article, timeit=True)
            return soup_article
        except:
            print('problem in doi : ', doi)
        return ''


    def get_abstract_article(self, soup_article):
        text = ''
        abstract = soup_article.find(name='div', attrs={'class': 'abstract-content'})
        if abstract:
            text = abstract.text
            text = text.replace('\nAbstract : ', '')
        return text

    def get_fields_article(self, soup_article):
        fields = self.hal_field
        field_elt = soup_article.find(name='blockquote', attrs={'style': 'margin-left:65px;margin-top:-15px;'})
        if field_elt:
            fields += ', ' + field_elt.find('strong').text.replace('/', ',').strip()
        return fields

    def get_keywords(self, soup_article):
        keywords_elt = soup_article.find(name='div', attrs={'class': 'keywords'})
        if keywords_elt:
            keywords = keywords_elt.text.replace('\n\nKeywords :\n', '').replace('\n\n', '').replace('\n', ', ').strip()
            return keywords
        return ''

    def get_nb_pages(self):
        path = self.path + '1'
        soup = self.get_soup(path, timeit=False)
        total_pages_soup = soup.find(name='ul', attrs={'class': 'pagination pagination-sm'}).find_all('li')[-1]
        total_pages = total_pages_soup.find('a')['href'].split('page=')[-1]
        return total_pages

    def get_soups(self,first_page,last_page):
      range_ = range(first_page, last_page + 1)
      for page in tqdm(range_, total=len(range_)):
            path = self.path + str(page)
            soup_page = self.get_soup(path, timeit=True)
            self.soup[page] = soup_page

    def get_docs(self):
        print('First data..')
        # soups = [BeautifulSoup(soup_df) for soup_df in soups_df['0']]
        for page in tqdm(self.soup):
            soup_page = self.soup[page]
            divs = self.get_divs_page(soup_page)
            dois, divs_filtered = self.get_dois_page_and_divs_filtered(divs)
            self.docs['doi']+= dois
            self.docs['title']+= self.get_titles_page(divs_filtered)
            self.docs['date']+= self.get_years_pages(divs_filtered,dois)
            self.docs['hal_address']+= self.get_hal_addresses_page(divs_filtered)
            self.docs['authors']+= self.get_authors(divs_filtered)

        print('Abstracts..')
        zip_ = zip(self.docs['doi'], self.docs['hal_address'])
        for doi, hal_address in tqdm(zip_, total=len(self.docs['doi'])):
            soup_article = self.get_soup_article(hal_address,doi)
            if soup_article:
                try:
                    abstract = self.get_abstract_article(soup_article)
                except:
                    abstract=''

                try:
                    fields = self.get_fields_article(soup_article)
                except:
                    fields= ''

                try:
                    keywords = self.get_keywords(soup_article)
                except:
                    keywords= ''

                try:
                    journal = self.get_journals_page(soup_article)
                except:
                    journal=''
            else:
                abstract,fields,keywords='','',''

            self.docs['abstract'].append(abstract)
            self.docs['fields'].append(fields)
            self.docs['keywords'].append(keywords)
            self.docs['journal'].append(journal)

