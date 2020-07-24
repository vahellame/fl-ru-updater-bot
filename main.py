# -*- coding: utf-8 -*-

import requests
import psycopg2
import requests
import urllib3
import socket

from bs4 import BeautifulSoup

from psycopg2.extras import RealDictCursor
from threading import Thread

from config import *

def fetch_projects_links_from_file():
    with open("projects.txt", "r") as f:
        project_links = f.readlines()

    for i in range(len(project_links)):
        project_links[i] = project_links[i][:-1]

    return project_links


def clean_projects_file():
    with open("projects.txt", "r") as f:
        project_links = f.readlines()
    if len(project_links) > 100:
        project_links = project_links[:40]
    with open("projects.txt", "w") as f:
        for project_link in project_links:
            f.write(f"{project_link}\n")


def fetch_projects_links_from_site():
    root_resp = requests.get("https://www.fl.ru/projects/")
    root_soup = BeautifulSoup(root_resp.text, 'lxml')

    root_soup_project_links = []
    for a in root_soup.find_all('a', href=True):
        link = str(a['href'])
        if "/projects/" in link and ".html" in link:
            root_soup_project_links.append(link)
    return root_soup_project_links


def add_new_projects_to_file(new_projects_links):
    with open("projects.txt", "a") as f:
        for project_link in new_projects_links:
            f.write(f"{project_link}\n")


def fetch_users():
    users = [
        {
            "name": "john",
            "project_types": ["hello", "friend"]
        }
    ]
    return users


def send_project(user, project_link):
    pass


def notify_users(new_projects_links):
    projects_types = {}
    users = fetch_users()

    for project_link in new_projects_links:
        projects_types[project_link] = []

        project_resp = requests.get("https://www.fl.ru" + project_link)
        project_soup = BeautifulSoup(project_resp.text, 'lxml')

        for a in project_soup.find_all('a', href=True):
            link = str(a['href'])
            if "/freelancers/" in link and len(link) > 13:
                projects_types[project_link].append(link)

    for project_link in projects_types:
        for projects_type_local in projects_types[project_link]:
            for user in users:
                if projects_type_local in user["types"]:
                    send_project(user, project_link)


def parse_and_send_projects():
    while True:
        file_projects_links = fetch_projects_links_from_file()
        if len(file_projects_links) > 40:
            clean_projects_file()
        site_projects_links = fetch_projects_links_from_site()

        new_projects_links = list(set(site_projects_links) - set(file_projects_links))

        if len(new_projects_links) > 0:
            add_new_projects_to_file(new_projects_links)
            notify_users(new_projects_links)


if __name__ == '__main__':
    pass
