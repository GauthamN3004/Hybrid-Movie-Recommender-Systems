#imdb poster scraping
from bs4 import BeautifulSoup
import requests

def get_poster(imdb_id):
    url = "https://www.imdb.com/title/tt"+str(imdb_id)+"/"
    req = requests.get(url).text
    soup = BeautifulSoup(req,"lxml")
    for div in soup.find_all("div",class_ = "poster"):
        a_tag = div.find('a')
        img_tag = a_tag.find('img')
        return img_tag["src"]
    return ''
