from bs4 import BeautifulSoup
from naimai.crawlers.issn_crawler import ISSN_crawler
from tqdm.notebook import tqdm

class doij_crawler:
  def __init__(self,html):
    self.soup = BeautifulSoup(html)
    self.cards = []
    self.docs = {'title': [], 'authors': [], 'date': [], 'fields': [], "abstract": [], "doi": [],
                     "numCitedBy": [], "numCiting": [], 'journals': []}

  def get_cards(self):
    self.cards=self.soup.find_all(name="li", attrs={"class": "card search-results__record"})

  def get_journal(self,card):
    heading = card.find(name="h3", attrs={"class": "search-results__heading"})
    return heading.text.strip()

  def get_issn(self,card):
    heading = card.find(name="h3", attrs={"class": "search-results__heading"})
    issn = heading.find(name="a")['href'].split('toc')[1][1:]
    return issn

  def get_fields(self,card):
    listing = card.find(name='div', attrs={'class': 'search-results__body'})
    listing_lists = listing.find_all(name='ul')
    return [elt.text for elt in listing_lists[1].find_all(name='li')]

  def get_data_with_issn(self,issn):
    cw = ISSN_crawler(issn=issn,field_issn='')
    try:
      cw.get_docs(show_tqdm=False)
      return cw.docs
    except:
      return

  def get_docs(self,page_start=0,page_end=-1):
    self.get_cards()
    for card in tqdm(self.cards)[page_start:page_end]:
      issn = self.get_issn(card)
      issn_docs = self.get_data_with_issn(issn)
      if issn_docs:
        self.docs['abstract'].append(issn_docs['abstract'])
        if self.docs['abstract']:
          self.docs['title'].append(issn_docs['title'])
          self.docs['authors'].append( issn_docs['authors'])
          self.docs['date'].append( issn_docs['date'])
          self.docs['doi'].append(issn_docs['doi'])
          self.docs['numCitedBy'].append(issn_docs['numCitedBy'])

          self.docs['journals'].append(self.get_journal(card))
          self.docs['fields'].append(self.get_fields(card))

