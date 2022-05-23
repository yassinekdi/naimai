from bs4 import BeautifulSoup
from naimai.crawlers.issn_crawler import ISSN_crawler
from tqdm.notebook import tqdm
import random
import time

class doij_crawler:
  def __init__(self,html):
    self.soup = BeautifulSoup(html,features="lxml")
    self.cards = []
    self.docs = {'title': [], 'authors': [], 'date': [], 'fields': [], "abstract": [], "doi": [],
                     "numCitedBy": [], "numCiting": [], 'journals': []}

    self.get_cards()

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

  def get_dois(self,t_min=2, t_max=5):
      for idx,card in tqdm(enumerate(self.cards), total=len(self.cards)):
          issn = self.get_issn(card)
          cw = ISSN_crawler(issn=issn, field_issn='')
          try:
              print('idx: ', idx)
              cw.get_dois(idx_start=0,idx_finish=-1)
          except:
              print('problem in idx : ', idx)
          self.docs['doi']+=cw.docs['doi']
          slp = random.randint(t_min, t_max)
          time.sleep(slp)

  def get_docs(self, idx_start=0, idx_end=-1):
    for card in tqdm(self.cards[idx_start:idx_end]):
      issn = self.get_issn(card)
      issn_docs = self.get_data_with_issn(issn)
      if issn_docs:
        self.docs['abstract']+=issn_docs['abstract']
        if self.docs['abstract']:
          self.docs['title']+=issn_docs['title']
          self.docs['authors']+= issn_docs['authors']
          self.docs['date']+= issn_docs['date']
          self.docs['doi']+=issn_docs['doi']
          self.docs['numCitedBy']+=issn_docs['numCitedBy']

          self.docs['journals']+=self.get_journal(card)
          self.docs['fields']+=self.get_fields(card)

