import requests
import json

from bs4 import BeautifulSoup

projects_types_dict = {}

resp = requests.get("https://www.fl.ru/projects/")
soup = BeautifulSoup(resp.text, 'lxml')
projects = soup.find_all("a", class_="b-layout__link b-layout__link_fontsize_11")

for project in projects:
    project_type_link = project["href"]
    project_type_name = str(project.contents[0])
    project_type_resp = requests.get("https://www.fl.ru" + project_type_link)
    project_type_soup = BeautifulSoup(project_type_resp.text, 'lxml')
    project_types_local = project_type_soup.find_all("a", class_="b-cat__link")

    projects_types_dict[project_type_link[13:]] = {
        "name": project_type_name,
        "local_types": {}
    }

    for project_type_local in project_types_local:
        project_type_local_name = project_type_local.contents[0][26:-44]
        project_type_local_link = str(project_type_local["href"])[13:-1]
        projects_types_dict[project_type_link[13:]]["local_types"][project_type_local_link] = project_type_local_name

print(projects_types_dict)

with open('project_types_names.json', 'w', encoding="utf-8") as f:
    json.dump(projects_types_dict, f, ensure_ascii=False, indent=4, sort_keys=False)