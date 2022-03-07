from bs4 import BeautifulSoup
import re
from tqdm.notebook import tqdm

def extract_author_name(contrib):
    try:
        lname = contrib.find('surname').text
        fname = contrib.find('given-names').text
        return fname + ' ' + lname
    except:
        return ''

class Pubmed_Crawler:
    def __init__(self, handle, database):
        self.xml_soup = BeautifulSoup(handle,'lxml')
        self.database = database
        self.docs = {'title': [], 'authors': [], 'year': [], "abstract": [], "doi": [],
                     "database": [], 'journal': [], 'body': []}

    # def read_file(self):
    #     xml_file = open(self.xml_filename, 'r')
    #     self.xml_soup = BeautifulSoup(xml_file, "lxml")

    def get_articles(self):
        return self.xml_soup.find_all('article')

    def get_doi(self, article):
        doi = article.find(name='article-id', attrs={'pub-id-type': 'doi'})
        if doi:
            return doi.text
        return

    def get_title(self, article):
        title = article.find('article-title')
        if title:
            return title.text
        return

    def get_year(self, article):
        year = article.find('year')
        if year:
            return year.text
        return

    def get_authors(self, article):
        authors_contribs = article.find_all(name='contrib', attrs={'contrib-type': 'author'})
        return [extract_author_name(contrib) for contrib in authors_contribs]

    def get_journal(self, article):
        journal = article.find('journal-title')
        if journal:
            return journal.text
        return

    def get_abstract(self, article):
        abstract_soup = article.find('abstract')
        if abstract_soup:
            abstract_elements = abstract_soup.find_all('sec')
            if abstract_elements :
              return {elt.find('title').text: [elt.text.strip() for elt in elt.find_all('p')] for elt in abstract_elements}
            else:
              return {'text': abstract_soup.text}
        return


    def get_body(self, article):
        body_elements = article.find_all(name='sec', id=re.compile('sec\d'))
        return {elt.find('title').text: [elt.text.strip() for elt in elt.find_all('p')] for elt in body_elements}

    def get_docs(self):
        articles = self.get_articles()
        for article in tqdm(articles):
            abstract = self.get_abstract(article)
            if abstract:
                self.docs['abstract'].append(abstract)
                self.docs['title'].append(self.get_title(article))
                self.docs['authors'].append(self.get_authors(article))
                self.docs['year'].append(self.get_year(article))
                self.docs['doi'].append(self.get_doi(article))
                self.docs['database'].append(self.database)
                self.docs['journal'].append(self.get_journal(article))
                self.docs['body'].append(self.get_body(article))
        print('>> Done!')