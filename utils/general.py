import pickle, gzip, pickletools
import requests
from bs4 import BeautifulSoup

def load_gzip(path):
    with gzip.open(path, 'rb') as f:
        p = pickle.Unpickler(f)
        return p.load()



def save_gzip(path,obj):
    with gzip.open(path, "wb") as f:
        pickled = pickle.dumps(obj)
        optimized_pickle = pickletools.optimize(pickled)
        f.write(optimized_pickle)

def get_soup(path):
    header = {}
    header[
        'User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    soup = BeautifulSoup(requests.get(path, headers=header, timeout=20).content, 'html.parser')
    return soup