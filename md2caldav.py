import re
import os
import glob
import caldav
import argparse
import configparser

from datetime import datetime
from tabulate import tabulate

def find_and_strip_eta(text, eta_initial=None):
    eta = eta_initial
    text_strip = text

    eta_match = re.search(r'\(*[0-9]{4}-[0-9]{2}-[0-9]{2}\)*', text)
    if eta_match != None:
        eta_text = re.sub(r'[\(\)]', '', eta_match.group()) # TODO make this always match last
        eta = datetime.strptime(eta_text, '%Y-%m-%d').date()
        text_strip = text.replace(eta_match.group(), '').strip()

    return eta, text_strip

def get_todos_from_md(md_text, list_name):
    todos_match = re.search(r'(^.*(?:\n|^)(?:- \[[^\]]*\] .*(?:\n- \[[^\]]*\] .*)+))', md_text, flags=re.MULTILINE)
    if todos_match == None:
        return []

    eta_list, list_name = find_and_strip_eta(list_name)

    todos = []
    for group in todos_match.groups():
        lines = group.splitlines()
        header, todos_text = lines[0], lines[1:]
        eta_header, header = find_and_strip_eta(header, eta_initial=eta_list)

        for todo_text in todos_text:
            eta, todo_text = find_and_strip_eta(todo_text, eta_initial=eta_header)
            todos.append({
                'calendar': list_name,
                'summary': todo_text.replace('- [ ] ', ''),
                'eta': eta
            })

    return todos

def get_todos_from_repo(repo_path):
    todos = []

    for path in glob.glob(os.path.join(repo_path, '**/*.md'), recursive=True):
        with open(path, 'r') as f:
            md_text = f.read()
            list_name = os.path.splitext(path.replace(repo_path, '')[1:])[0]
            todos += get_todos_from_md(md_text, list_name)

    return todos

def main():
    parser = argparse.ArgumentParser('md2caldav', description='Markdown to CalDAV bridge for task synchronization')
    parser.add_argument('-c', '--config', help='Path to configuration file', default='config.cfg')
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.config)

    todos = get_todos_from_repo(config.get('Repository', 'Path'))
    print(tabulate(todos, headers='keys', tablefmt='fancy_outline'))

    #with caldav.DAVClient(
    #    url=config.get('Server', 'url'),
    #    username=config.get('Server', 'username'),
    #    password=config.get('Server', 'password')
    #) as client:
    #    principal = client.principal()

if __name__ == '__main__':
    main()
