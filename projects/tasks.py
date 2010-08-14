import os
import re
import glob
import fnmatch
from celery.decorators import task
from projects.models import Project, Conf
from projects.utils import get_project_path, find_file

#ghetto_hack = re.compile(r'^(?P<key>\s*) = \s*u?[\'\"](?P<value>.*)[\'\"]$')
ghetto_hack = re.compile(r'(?P<key>.*)\s*=\s*u?[\'\"](?P<value>.*)[\'\"]')

@task
def update_docs(slug, type='git'):
    project = Project.objects.get(slug=slug)
    path = get_project_path(project)
    if not os.path.exists(path):
        os.makedirs(path)
    os.chdir(path)
    if os.path.exists(os.path.join(path, project.slug)):
        os.chdir(project.slug)
        if type is 'git':
            command = 'git fetch && git reset --hard origin/master'
            print command
            os.system(command)
    else:
        if type is 'git':
            command = 'git clone %s.git %s' % (project.github_repo, project.slug)
            print command
            os.system(command)
        elif type is 'hg':
            os.system('hg clone ')
    build_docs(path, project=project)


def build_docs(path, project=None):
    os.chdir(path)
    matches = find_file('Makefile')
    if len(matches) == 1:
        make_dir = matches[0].replace('/Makefile', '')
        os.chdir(make_dir)
        os.system('make html')

    matches = find_file('conf.py')
    if len(matches) == 1:
        make_dir = matches[0].replace('/conf.py', '')
        os.chdir(make_dir)
        #Hack this for now...
        #from .conf import copyright, project, version, release, html_theme 
        #print release, html_theme
        lines = open('conf.py').readlines()
        data = {} 
        for line in lines:
            for we_care in ['copyright', 'project', 'version', 'release', 'html_theme']:
                if we_care in line:
                    match = ghetto_hack.search(line)
                    if match:
                        data[match.group(1).strip()] = match.group(2).strip()
        conf = Conf.objects.get_or_create(project=project)[0]
        conf.copyright = data['copyright']
        conf.version = data['version']
        conf.theme = data['html_theme']
        conf.save()
