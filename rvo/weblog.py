"""Script to create index, date and tag pages.
"""
import codecs
import datetime
import os
import sys
import time

from docutils.core import publish_parts
from docutils.writers.html4css1 import Writer
from jinja2 import Environment
from jinja2 import PackageLoader

from rvo.rst import setup_for_plain_docutils

TAGSTART = '.. tags::'
TECHNORATI_TAGS = ['europython2009']


jinja_env = Environment(loader=PackageLoader('rvo', 'templates'))


def utf8_open(filepath, mode='r'):
    return codecs.open(filepath, mode, 'utf-8')


def conditional_write(filename, new):
    if os.path.exists(filename):
        old = utf8_open(filename, 'r').read()
    else:
        old = None
    if new != old:
        utf8_open(filename, 'w').write(new)
        print '.',


class Bucket(object):
    """A bucket of entries (tag/day) or other buckets (year/month)"""

    tocdepth = 1
    sort_entries = False

    def __init__(self, name, directory):
        self.name = name
        self.dir = directory
        self.items = []

    @property
    def nice_name(self):
        return self.name

    @property
    def size(self):
        return len(self.items)

    def __len__(self):
        return self.size

    def append(self, something):
        self.items.append(something)

    @property
    def filename(self):
        return os.path.join(self.dir, 'index.txt')

    def create_files(self):
        """At least create ourselves. Subclasses should ensure recursion"""
        self.create_file()

    def create_file(self):
        content = []
        content.append(self.nice_name)
        content.append('#' * len(self.nice_name))
        content.append('')
        content += self.subitems()
        content.append('')
        content += self.overview()
        conditional_write(self.filename, '\n'.join(content))

    def subitems(self):
        """Return link block at the start of the page"""
        result = []
        result.append('.. toctree::')
        result.append('    :maxdepth: %s' % self.tocdepth)
        result.append('')
        if self.sort_entries:
            self.items.sort()
        for item in self.items:
            link = item.filename.replace(self.dir, '')
            link = link.lstrip('/')
            result.append('    ' + link)
        return result

    def overview(self):
        return ''


class Year(Bucket):
    """A year contains months"""
    tocdepth = 4

    @property
    def size(self):
        return sum([item.size for item in self.items])

    @property
    def nice_name(self):
        return 'Weblog entries for ' + self.name

    def create_files(self):
        self.create_file()
        for item in self.items:
            item.create_files()


class Month(Bucket):
    """A month contains days"""
    tocdepth = 3

    @property
    def size(self):
        return sum([item.size for item in self.items])

    @property
    def nice_name(self):
        parts = self.dir.split('/')
        assert parts[-1] == self.name
        year = parts[-2]
        month = datetime.date(2000, int(self.name), 1).strftime('%B')
        return "%s %s" % (month, year)

    def create_files(self):
        self.create_file()
        for item in self.items:
            item.create_files()


class Day(Bucket):
    """A day contains entries"""
    tocdepth = 2
    sort_entries = True

    @property
    def nice_name(self):
        parts = self.dir.split('/')
        assert parts[-1] == self.name
        month = parts[-2]
        year = parts[-3]
        return "%s-%s-%s" % (year, month, self.name)


class Tag(Bucket):
    """A tag contains entries"""
    sort_entries = True

    @property
    def filename(self):
        return os.path.join(self.dir, 'tags/%s.txt' % self.name)

    def __cmp__(self, other):
        return cmp(self.size, other.size)

    def subitems(self):
        """Return link block at the start of the page"""
        result = []
        result.append('.. toctree::')
        result.append('    :maxdepth: %s' % self.tocdepth)
        result.append('')
        self.items.sort()
        for item in self.items:
            link = item.filename.replace(self.dir, '')
            link = link.lstrip('/')
            result.append('    %s %s <../%s>' % (
                item.ymd, item.title, link))
        return result


class Entry(object):
    """Extracted info from weblog entry *.txt file.

    We need the path, the title and the tags.

    """

    def __init__(self, filepath):
        self.filename = filepath
        self.lines = utf8_open(filepath).read().split(u'\n')
        self.title = self.lines[0].strip()
        tagline = [line for line in self.lines if TAGSTART in line]
        self.tags = []
        if tagline:
            tagline = tagline[0].replace(TAGSTART, '')
            self.tags = tagline.split(',')
            self.tags = [tag.strip() for tag in self.tags]
        # modification time
        self.last_modified = time.gmtime(os.path.getmtime(self.filename))
        self.last_modified = time.strftime('%Y-%m-%dT%H:%M', self.last_modified)

    def __cmp__(self, other):
        by_date = cmp(other.ymd, self.ymd) # reverse
        if by_date:
            return by_date
        return cmp(self.title, other.title)

    @property
    def ymd(self):
        """Return yyyy-mm-dd date"""
        parts = self.filename.split('/')
        day = parts[-2]
        month = parts[-3]
        year = parts[-4]
        return "%s-%s-%s" % (year, month, day)

    def assign_to_tags(self, tag_dict, weblogdir):
        """Append ourself to tags"""
        for tag in self.tags:
            if tag not in tag_dict:
                tag_dict[tag] = Tag(tag, weblogdir)
            tag_dict[tag].append(self)

    @property
    def url(self):
        """Return url relative to weblog root (excluding starting slash)"""
        return self.filename.replace('.txt', '.html').replace('source/', '')

    @property
    def atom_content(self):
        """Return rendered html for atom content"""
        # Filter out first two lines (title and underline)
        lines = self.lines[2:]
        lines = [line for line in lines if not '.. tags::' in line]
        # render to html
        html_writer = Writer()
        content = publish_parts('\n'.join(lines),
                                writer=html_writer)
        html = content['html_body']
        html = html.replace('&nbsp;', ' ')
        return html


class Weblog(object):
    """Wrapper around weblog dir"""

    def __init__(self, weblogdir):
        self.weblogdir = weblogdir
        if 'weblog' in self.weblogdir:
            self.name = "Reinout van Rees' weblog"
            self.subtitle = "Python, grok, books, history, faith, etc."
            self.base_url = 'http://reinout.vanrees.org/'
            self.target_dir = os.path.join(self.weblogdir, '..', '..',
                                           'build', 'html', 'weblog')
        self.tags = {}
        self.years = []
        self.all = []

    def assign_entries(self):
        """Assign all found entries to their year and tag"""
        for yearname in sorted(os.listdir(self.weblogdir)):
            try:
                int(yearname)
            except ValueError:
                continue
            yeardir = os.path.join(self.weblogdir, yearname)
            year = Year(yearname, yeardir)
            self.years.append(year)
            for monthname in sorted(os.listdir(yeardir)):
                try:
                    int(monthname)
                except ValueError:
                    continue
                monthdir = os.path.join(yeardir, monthname)
                month = Month(monthname, monthdir)
                year.append(month)
                for dayname in sorted(os.listdir(monthdir)):
                    try:
                        int(dayname)
                    except ValueError:
                        continue
                    daydir = os.path.join(monthdir, dayname)
                    day = Day(dayname, daydir)
                    month.append(day)
                    for entryname in os.listdir(daydir):
                        if entryname == 'index.txt':
                            continue
                        if entryname.endswith('.txt'):
                            path = os.path.join(daydir, entryname)
                            entry = Entry(path)
                            entry.assign_to_tags(self.tags, self.weblogdir)
                            day.append(entry)
                            self.all.append(entry)

    def create_files(self):
        for tag in self.tags.values():
            tag.create_files()
        for year in self.years:
            year.create_files()
        self.homepage()
        self.tagpage()
        # TODO: tag cloud?
        # TODO: tag cloud of last 50 entries?

    def homepage(self):
        content = []
        content.append(self.name)
        content.append('#' * len(self.name))
        content.append('')
        content += self.subitems()
        content.append('')
        content += self.overview()
        filename = os.path.join(self.weblogdir, 'index.txt')
        conditional_write(filename, '\n'.join(content))

    def tagpage(self):
        content = []
        title = 'Tag overview'
        content.append(title)
        content.append('#' * len(title))
        content.append('')
        content.append('.. toctree::')
        content.append('    :maxdepth: 1')
        content.append('')
        tags = self.tags.values()
        tags.sort(reverse=True)
        for tag in tags:
            content.append('    %s (%s) <%s.txt>' % (
                tag.name, tag.size, tag.name))
        content.append('')
        filename = os.path.join(self.weblogdir, 'tags/index.txt')
        conditional_write(filename, '\n'.join(content))

    def subitems(self):
        """Show most recent weblog entries"""
        result = []
        NUMBER = 10
        entries = self.all[-NUMBER:]
        entries.reverse()
        for entry in entries:
            parts = entry.filename.split('/')
            link = '/'.join(parts[-4:])
            link = link.replace('.txt', '.html')
            header = '`%s <%s>`_' % (entry.title, link)
            result.append(header)
            result.append('=' * len(header))
            result.append('')
            result.append(entry.ymd)
            result.append('')
            for line in entry.lines[2:]:
                line = line.replace('.. tags::', '.. roottags::')
                result.append(line)
            result.append('')
        return result

    def overview(self):
        """Return link block at the end of the page"""
        result = []
        title = "Overview by year"
        result.append(title)
        result.append('=' * len(title))
        result.append('')
        result.append("`Statistics </weblog/statistics.html>`_: charts of "
                      "posts per year and per month.")
        result.append('')
        result.append('.. toctree::')
        result.append('    :maxdepth: 1')
        result.append('')
        for item in self.years:
            link = item.filename.replace(self.weblogdir, '')
            link = link.lstrip('/')
            result.append('    ' + link)
        result.append('    tags/index.txt')
        return result

    def create_atom(self):
        self.all.sort()
        self.all.reverse()
        atom_templ = jinja_env.get_template('atom.xml')
        # Main atom file
        last_10 = self.all[-10:]
        last_10.reverse()
        target_name = os.path.join(self.target_dir, 'atom.xml')
        utf8_open(target_name, 'w').write(
            atom_templ.render(base_url=self.base_url,
                              title=self.name,
                              subtitle=self.subtitle,
                              feedfile='atom.xml',
                              entries=last_10))
        # Planet plone + planet zope
        plone_entries = [entry for entry in self.all
                         if 'plone' in entry.tags
                         or 'grok' in entry.tags
                         or 'python' in entry.tags
                         or 'europython2009' in entry.tags
                         or 'buildout' in entry.tags
                         or 'zope' in entry.tags]
        if plone_entries: # Not in preken weblog ;-)
            plone_entries = plone_entries[-10:]
            plone_entries.reverse()
            target_name = os.path.join(self.target_dir, 'plonefeed.xml')
            utf8_open(target_name, 'w').write(
                atom_templ.render(base_url=self.base_url,
                                  title=self.name,
                                  feedfile='plonefeed.xml',
                                  subtitle=self.subtitle,
                                  entries=plone_entries))
        # planet python
        # Planet plone
        python_entries = [entry for entry in self.all
                          if 'plone' in entry.tags
                          or 'grok' in entry.tags
                          or 'python' in entry.tags
                          or 'europython2009' in entry.tags
                          or 'buildout' in entry.tags
                          or 'django' in entry.tags
                          or 'djangocon' in entry.tags
                          or 'zope' in entry.tags]
        if python_entries: # Not in preken weblog ;-)
            python_entries = python_entries[-10:]
            python_entries.reverse()
            target_name = os.path.join(self.target_dir, 'pythonfeed.xml')
            utf8_open(target_name, 'w').write(
                atom_templ.render(base_url=self.base_url,
                                  title=self.name,
                                  subtitle=self.subtitle,
                                  feedfile='pythonfeed.xml',
                                  entries=python_entries))

        django_entries = [entry for entry in self.all
                          if 'django' in entry.tags
                          or 'djangocon' in entry.tags]
        if django_entries:
            django_entries = django_entries[-10:]
            django_entries.reverse()
            target_name = os.path.join(self.target_dir, 'djangofeed.xml')
            utf8_open(target_name, 'w').write(
                atom_templ.render(base_url=self.base_url,
                                  title=self.name,
                                  subtitle=self.subtitle,
                                  feedfile='djangofeed.xml',
                                  entries=django_entries))


    def create_for_homepage(self):
        """Create html snippet for inclusion in homepage"""
        self.all.sort()
        self.all.reverse()
        snippet_templ = jinja_env.get_template('homepagesnippet.html')
        # Main atom file
        last_5 = self.all[-5:]
        last_5.reverse()
        target_name = os.path.join(self.target_dir, 'snippet.html')
        utf8_open(target_name, 'w').write(
            snippet_templ.render(base_url=self.base_url,
                                 entries=last_5))

    def create_stats(self):
        """Create html page with statistics"""
        statistic_templ = jinja_env.get_template('statistics.html')
        target_name = os.path.join(self.target_dir, 'statistics.html')
        years = [dict(name=year.name, number=len(year)) for year in
                 self.years]

        maximum = max([y['number'] for y in years])
        base = 'http://chart.apis.google.com/chart?'
        size = 'chs=600x200'
        colors = 'chco=4444FF'
        data = 'chd=t:%s' % ','.join([str(y['number']) for y in years])
        maxmin = 'chds=0,%d' % maximum
        type_ = 'cht=bvg'
        #legend = 'chdl=posts+per+year'
        axis_def = 'chxt=x,y'
        x = '|'.join([str(y['name']) for y in years])
        axis_val = 'chxl=0:|%s|1:|0|%d' % (x, maximum)
        #labels = 'chl=Hello|World'
        yeargraph = base + '&amp;'.join([size, colors, data, maxmin, type_,
                                         axis_def, axis_val])


        months = []
        for year in self.years:
            months += [dict(name=' '.join([month.name, year.name]),
                            month=month.name,
                            year=year.name,
                            number=len(month))
                       for month in year.items]
            # Special case: dec 2005... that one is missing.
            if year.name == '2005':
                months.append(dict(name='12 2005',
                                   month='12',
                                   year='2005',
                                   number=0))
        average = float(months[0]['number'])
        ratio = 0.2
        maximum = 0
        for month in months:
            amount = month['number']
            if amount > maximum:
                maximum = amount
            average = average + ratio * amount
            average = average / (1.0 + ratio)
            month['average'] = average
        global_average = sum([month['number'] for month in months])
        global_average = global_average / len(months)
        base = 'http://chart.apis.google.com/chart?'
        size = 'chs=600x300'
        colors = 'chco=BBBBFF,4444FF,BBBBBB'
        data = 'chd=t:%s|%s|%s' % (
            ','.join([str(m['number']) for m in months]),
            ','.join([str(round(m['average'])) for m in months]),
            ','.join([str(global_average) for m in months]))
        maxmin = 'chds=0,%d,0,%d,0,%d' % (maximum, maximum, maximum)
        linestyle = 'chls=1,1,0|5,1,0|1,1,0'
        type_ = 'cht=lc'
        legend = 'chdl=posts+per+month|moving+average|average'
        axis_def = 'chxt=x,x,y'
        in_between = len(months) / 4.0
        x1 = []
        x2 = []
        for i in range(5):
            index = int(round(i * in_between))
            if index >= len(months):
                index = len(months) - 1
            x1.append(months[index]['month'])
            x2.append(months[index]['year'])
        x1 = '|'.join(x1)
        x2 = '|'.join(x2)
        axis_val = 'chxl=0:|%s|1:|%s|2:|0|%s' % (x1, x2, maximum)
        #labels = 'chl=Hello|World'
        monthgraph = base + '&amp;'.join([size, colors, data, maxmin, type_,
                                          linestyle,
                                          legend, axis_def, axis_val])

        utf8_open(target_name, 'w').write(
            statistic_templ.render(years=years,
                                   yeargraph=yeargraph,
                                   months=months,
                                   maximum=maximum,
                                   monthgraph=monthgraph))



def main():
    if len(sys.argv) < 2:
        print "Missing start dir of weblog"
        sys.exit(1)
    weblogdir = sys.argv[1]
    setup_for_plain_docutils()
    weblog = Weblog(weblogdir)
    weblog.assign_entries()
    weblog.create_files()
    weblog.create_atom()
    weblog.create_for_homepage()
    weblog.create_stats()
