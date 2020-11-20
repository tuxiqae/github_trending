import requests as r
from bs4 import BeautifulSoup as bs
import pandas as pd
import json
import re


def get_url(url):
    res = r.get(url)
    if res.status_code != 200:
        print("Got status code " + str(res.status_code) + " from: " + res.url)
        exit(1)

    return res


def trending_repos(res):
    props = {'names': list(), "owners": list(), "languages": list(), "stars": list()}

    doc = bs(res.text, "lxml")

    for repo in doc.find_all("article", class_="Box-row"):
        populate_names(repo, props)
        populate_languages(repo, props)
        populate_stars(repo, props)

    print(json.dumps(props))

    return pd.DataFrame(props)


def name_printer(names, owners):
    for i in range(len(names)):
        print(owners[i] + "/" + names[i])


def populate_names(elem, list_dict):
    owner, _, name = elem.find("h1", class_="h3 lh-condensed").text.strip().split()
    list_dict["owners"].append(owner)
    list_dict["names"].append(name)


def populate_languages(elem, list_dict):
    if (lang := elem.find("span", itemprop="programmingLanguage")) is not None:
        list_dict["languages"].append(lang.text)
    else:
        list_dict["languages"].append("N/A")


def populate_stars(elem, list_dict):
    list_dict["stars"].append(int(elem.find(href=re.compile("stargazers$")).text.strip().replace(",", "")))


def export(filename, data_frame):
    fh = open(filename, 'w')
    fh.write(data_frame.to_csv())
    fh.close()


# def trending_devs(URL):
#

if __name__ == '__main__':
    URL = "https://github.com/trending"
    df = trending_repos(get_url(URL))

    export('repos.csv', df)

    print(df)
