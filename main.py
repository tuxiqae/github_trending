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
    props = {
        'name': list(),
        "owner": list(),
        "language": list(),
        "description": list(),
        "stargazers": list(),
        "daily_stargazers": list(),
        "forks": list(),
        "top_contributors": list(),
    }

    doc = bs(res.text, "lxml")

    for repo in doc.find_all("article", class_="Box-row"):
        populate_names(repo, props)
        populate_languages(repo, props)
        populate_descriptions(repo, props)
        populate_stargazers(repo, props)
        populate_forks(repo, props)
        populate_daily_stars(repo, props)
        populate_top_contributors(repo, props)

    print(json.dumps(props))

    return pd.DataFrame(props)


def name_printer(names, owners):
    for i in range(len(names)):
        print(owners[i] + "/" + names[i])


def populate_names(elem, list_dict):
    owner, _, name = elem.find("h1", class_="h3 lh-condensed").text.strip().split()
    list_dict["owner"].append(owner)
    list_dict["name"].append(name)


def populate_languages(elem, list_dict):
    if (lang := elem.find("span", itemprop="programmingLanguage")) is not None:
        list_dict["language"].append(lang.text)
    else:
        list_dict["language"].append("N/A")


def populate_descriptions(elem, list_dict):
    if (desc := elem.find("p")) is not None:
        list_dict["description"].append(desc.text)
    else:
        list_dict["description"].append("N/A")


def populate_stargazers(elem, list_dict):
    list_dict["stargazers"].append(numstr_to_int(elem.find(href=re.compile("stargazers$")).text.strip()))


def populate_daily_stars(elem, list_dict):
    list_dict["daily_stargazers"].append(int(elem.find(string=re.compile("stars today$")).split()[0]))


def populate_forks(elem, list_dict):
    list_dict["forks"].append(numstr_to_int(elem.find("svg", class_="octicon-repo-forked").parent.text.strip()))


def populate_top_contributors(elem, list_dict):
    contrib_list = list()

    for contrib in elem.find(string=re.compile("Built by")).parent.find_all("a"):
        contrib_list.append(contrib["href"].replace("/", ""))

    list_dict["top_contributors"].append(contrib_list)


def numstr_to_int(numstr):
    return int(numstr.replace(",", ""))


def export(filename, data_frame):
    fh = open(filename, 'w')
    fh.write(data_frame.to_csv())
    fh.close()


if __name__ == '__main__':
    URL = "https://github.com/trending"
    df = trending_repos(get_url(URL))
    df["stars growth %"] = (df["daily_stargazers"] / df["stargazers"]) * 100
    export('repos.csv', df)

    print(df)
