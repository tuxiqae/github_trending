import argparse
import re

import pandas as pd
import requests as r
from bs4 import BeautifulSoup as Soup

__author__ = "Sagi Sarussi"
__copyright__ = "Copyright 2020, Sagi Sarussi"
__license__ = "GPL-3.0-or-later"
__version__ = "1.0.0"
__maintainer__ = "Sagi Sarussi"
__email__ = "sagis@sagis.dev"


def get_url(url, params):
    res = r.get(url, params=params)
    assert res.status_code == 200

    return res


def trending_repos(res):
    props = {
        "name": [],
        "owner": [],
        "language": [],
        "description": [],
        "stargazers": [],
        "stargazers for range": [],
        "forks": [],
        "top contributors": [],
    }

    for repo in Soup(res.text, "lxml").find_all("article", class_="Box-row"):
        populate_names(repo, props)
        populate_languages(repo, props)
        populate_descriptions(repo, props)
        populate_stargazers(repo, props)
        populate_forks(repo, props)
        populate_stars_for_range(repo, props)
        populate_top_contributors(repo, props)

    return pd.DataFrame(props)


def name_printer(names, owners):
    for i, _ in enumerate(names):
        print(owners[i] + "/" + names[i])


def populate_names(elem, list_dict):
    cls = r"h3 lh-condensed"
    owner, _, name = elem.find("h1", class_=cls).text.strip().split()
    list_dict["owner"].append(owner)
    list_dict["name"].append(name)


def populate_languages(elem, list_dict):
    if (lang := elem.find("span", itemprop="programmingLanguage")) is not None:
        list_dict["language"].append(lang.text)
    else:
        list_dict["language"].append("N/A")


def populate_descriptions(elem, list_dict):
    if (desc := elem.find("p")) is not None:
        list_dict["description"].append(desc.text.strip())
    else:
        list_dict["description"].append("N/A")


def populate_stargazers(elem, list_dict):
    list_dict["stargazers"].append(
        numstr_to_int(elem.find(href=re.compile(r"stargazers$")).text.strip()))


def populate_stars_for_range(elem, list_dict):
    query = r"(\d{1,3} stars today$)|(\d{1,3} stars this (week)|(month))"
    list_dict["stargazers for range"].append(
        numstr_to_int(elem.find(string=re.compile(query)).strip().split()[0]))


def populate_forks(elem, list_dict):
    cls = r"octicon-repo-forked"
    list_dict["forks"].append(
        numstr_to_int(elem.find("svg", class_=cls).parent.text.strip()))


def populate_top_contributors(elem, list_dict):
    contrib_list = []
    string = re.compile("Built by")
    for contrib in elem.find(string=string).parent.find_all("a"):
        contrib_list.append(contrib["href"].replace("/", ""))

    list_dict["top contributors"].append(contrib_list)


def numstr_to_int(numstr):
    return int(numstr.replace(",", ""))


def export(filename, data_frame):
    file_handle = open(filename, 'w')
    file_handle.write(data_frame.to_csv())
    file_handle.close()


def get_args():
    choices = ["daily", "weekly", "monthly"]

    parser = argparse.ArgumentParser(prog="github_trending.py",
                                     description="Scrape the most trending GitHub repositories.")
    parser.add_argument("-d", "--date_range",
                        type=str,
                        choices=choices,
                        default=choices[0],
                        action="store",
                        help="The date range to search in."
                        )

    parser.add_argument("-l", "--language",
                        type=str,
                        default="",
                        action="store",
                        help="The programming language to filter by.",
                        )

    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()

    URL = "https://github.com/trending/{lang}".format(lang=args.language)
    repos_df = trending_repos(get_url(URL, {"since": args.date_range}))
    repos_df["stars growth %"] = (repos_df["stargazers for range"] / repos_df["stargazers"]) * 100
    export('repos.csv', repos_df)

    print(repos_df)
