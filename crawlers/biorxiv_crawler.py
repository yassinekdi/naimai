import zipfile
from bs4 import BeautifulSoup
from tqdm.notebook import tqdm
import re

def get_authors(authors_contrib):
  last_name = authors_contrib.find('surname')
  first_name = authors_contrib.find('given-names')
  if last_name:
      return first_name.string + ' ' + last_name.string
  else:
      return ''


class bioRxiv_xml_data:
    def __init__(self):
        self.docs = {'title': [], 'authors': [], 'date': [], 'field_paper': [], "abstract": [], "doi": [],
                     "database": [], "file_name": []}

    def get_doi(self, bs):
        return bs.find_all(name="article-id")[0].string

    def get_topic(self, bs):
        try:
            return bs.find_all(name="subj-group", attrs={'subj-group-type': 'hwp-journal-coll'})[0].find('subject').string
        except:
            return ''

    def get_title(self, bs):
        try :
            return bs.find_all(name="title-group")[0].find('article-title').text
        except:
            return ''

    def get_authors(self, bs):
        try:
            authors_contrib = bs.find_all(name="contrib-group")[0].find_all(name="contrib",
                                                                            attrs={"contrib-type": "author"})
            authors = ', '.join([get_authors(elt) for elt in authors_contrib])
        except:
            authors=""
        return authors

    def get_year(self, bs):
        try :
            return bs.find("year").string
        except:
            return ''

    def get_abstract(self, bs):
        abstract = bs.find("abstract")
        if abstract:
            abstract = abstract.text
            abstract2 = re.sub('abstract', '', abstract, flags=re.I)
            return abstract2.replace('\n', ' ').strip()
        return ''

    def get_kwords(self, bs):
        kwords = bs.find("kwd-group")
        if kwords:
            return ', '.join([elt.string for elt in kwords.find_all('kwd')])
        else:
            return ''

    def get_xml_files(self, archive):
        listfiles = archive.namelist()
        return [elt for elt in listfiles if 'xml' in elt]

    def get_file_data(self, xml_file, xml_file_name):
        bs4_xml = BeautifulSoup(xml_file, "lxml")
        abstract = self.get_abstract(bs4_xml)
        if abstract:
            self.docs['title'].append(self.get_title(bs4_xml))
            self.docs['authors'].append(self.get_authors(bs4_xml))
            self.docs['date'].append(self.get_year(bs4_xml))
            self.docs['field_paper'].append(self.get_topic(bs4_xml))
            self.docs['abstract'].append(abstract)
            self.docs['doi'].append(self.get_doi(bs4_xml))
            self.docs['database'].append("bioRxiv")
            self.docs['file_name'].append(xml_file_name)

    def get_docs(self, path):
        archive = zipfile.ZipFile(path, 'r')
        list_xml_files = self.get_xml_files(archive)

        for fle in tqdm(list_xml_files):
            xml_file = archive.read(fle)
            self.get_file_data(xml_file, fle)
