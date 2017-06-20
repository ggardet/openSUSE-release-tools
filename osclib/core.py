from xml.etree import cElementTree as ET

import osc.core
from osc.core import get_dependson
from osc.core import http_GET
from osc.core import makeurl
from osc.core import show_project_meta

from osclib.memoize import memoize


@memoize(session=True)
def owner_fallback(apiurl, project, package):
    root = osc.core.owner(apiurl, package, project=project)
    owner = root.find('owner')
    if not owner or owner.get('project') == project:
        # Fallback to global (ex Factory) maintainer.
        root = osc.core.owner(apiurl, package)
    return root

@memoize(session=True)
def maintainers_get(apiurl, project, package=None):
    if package is None:
        meta = ET.fromstring(''.join(show_project_meta(apiurl, project)))
        return [p.get('userid') for p in meta.findall('.//person') if p.get('role') == 'maintainer']

    root = owner_fallback(apiurl, project, package)
    maintainers = [p.get('name') for p in root.findall('.//person') if p.get('role') == 'maintainer']
    if not maintainers:
        for group in [p.get('name') for p in root.findall('.//group') if p.get('role') == 'maintainer']:
            url = makeurl(apiurl, ('group', group))
            root = ET.parse(http_GET(url)).getroot()
            maintainers = maintainers + [p.get('userid') for p in root.findall('./person/person')]
    return maintainers

@memoize(session=True)
def package_list(apiurl, project):
    url = makeurl(apiurl, ['source', project], { 'expand': 1 })
    root = ET.parse(http_GET(url)).getroot()

    packages = []
    for package in root.findall('entry'):
        packages.append(package.get('name'))

    return sorted(packages)

@memoize(session=True)
def target_archs(apiurl, project):
    meta = show_project_meta(apiurl, project)
    meta = ET.fromstring(''.join(meta))
    archs = []
    for arch in meta.findall('repository[@name="standard"]/arch'):
        archs.append(arch.text)
    return archs

@memoize(session=True)
def depends_on(apiurl, project, repository, packages=None, reverse=None):
    dependencies = set()
    for arch in target_archs(apiurl, project):
        root = ET.fromstring(get_dependson(apiurl, project, repository, arch, packages, reverse))
        dependencies.update(pkgdep.text for pkgdep in root.findall('.//pkgdep'))

    return dependencies
