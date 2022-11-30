"""Script to create my /preken overview"""
import collections
import datetime
import logging
import os
import sys
import time
from functools import total_ordering

from rvo.rst import setup_for_plain_docutils
from rvo.weblog import conditional_write, utf8_open

logger = logging.getLogger(__name__)

BASE_URL = "http://reinout.vanrees.org/preken"
INFO_TYPES = {
    "kerk": "Kerken",
    "predikant": "Predikanten",
    "tekst": "Teksten",
    "datum": "Datum",
    "toegevoegd": "Toegevoegd",
    "tags": "Tags",
}


def sorted_by_size(dictionary):
    """Return dictionary keys, sorted by biggest key."""
    keys_and_size = [(key, len(dictionary[key])) for key in dictionary]
    keys_and_size.sort(key=lambda x: x[1])
    keys_and_size.reverse()
    return [key for key, size in keys_and_size]


class Sermonlog(object):
    """Wrapper around sermon directory."""

    def __init__(self, sermonlogdir):
        self.sermonlogdir = sermonlogdir
        self.years = collections.defaultdict(list)
        self.kerk = collections.defaultdict(list)
        self.predikant = collections.defaultdict(list)
        self.tekst = collections.defaultdict(list)
        self.tags = collections.defaultdict(list)

    def collect_entries(self):
        """Figure out the years and start sermon collecting in there."""
        for directory in os.listdir(self.sermonlogdir):
            if len(directory) != 4:
                # Not a 4-digit year directory!
                continue
            try:
                year = int(directory)
            except ValueError:
                # Not a real 4-digit thingy.
                continue
            self._collect_sermons(year)

    def _collect_sermons(self, year):
        """Collect sermons for one year directory."""
        year_dir = os.path.join(self.sermonlogdir, str(year))
        for sermon_file in os.listdir(year_dir):
            if not sermon_file.endswith(".txt"):
                continue
            if sermon_file == "index.txt":
                continue
            sermon = Sermon(year, year_dir, sermon_file)
            self.years[sermon.year].append(sermon)
            for info_type in INFO_TYPES:
                if info_type in ["datum", "toegevoegd"]:
                    continue
                for tag in getattr(sermon, info_type, None):
                    if tag is None:
                        continue
                    getattr(self, info_type)[tag].append(sermon)

    def write_years(self):
        for year in self.years:
            year_index = os.path.join(self.sermonlogdir, str(year), "index.txt")
            content = []
            content.append(str(year))
            content.append("#" * len(str(year)))
            content.append("")
            content.append(".. toctree::")
            content.append("    :maxdepth: 1")
            content.append("")
            sermons = self.years[year]
            sermons.sort()
            for sermon in sermons:
                content.append("    " + sermon.year_link)
            conditional_write(year_index, "\n".join(content))

    def write_index(self):
        total_index = os.path.join(self.sermonlogdir, "index.txt")
        content = []
        title = "Reinout's preeksamenvattingen"
        content.append(title)
        content.append("=" * len(title))
        content.append("")
        content.append("Meest recente preken")
        content.append("--------------------")
        content.append("")
        content.append(".. toctree::")
        content.append("    :maxdepth: 1")
        content.append("")
        for sermon in self.recent_ten():
            content.append("    %s" % sermon.full_link)
        content.append("")
        content.append("Jaren")
        content.append("-----")
        content.append("")
        content.append(".. toctree::")
        content.append("    :maxdepth: 1")
        content.append("")
        for year in sorted(self.years.keys()):
            content.append("    %s/index" % year)
        content.append("")
        for info_type in INFO_TYPES:
            if info_type in ["datum", "toegevoegd", "tekst"]:
                continue
            dirname = INFO_TYPES[info_type].lower()
            title = INFO_TYPES[info_type]
            content.append(title)
            content.append("-" * len(title))
            content.append("")
            info_items = getattr(self, info_type)
            content.append(".. toctree::")
            content.append("    :maxdepth: 1")
            content.append("")
            for info_item in sorted_by_size(info_items):
                content.append(
                    "    %s (%s) <%s/%s.txt>"
                    % (info_item, len(info_items[info_item]), dirname, info_item)
                )
            content.append("")
        conditional_write(total_index, "\n".join(content))

    def recent_ten(self):
        """Return ten most recent sermons."""
        two_recent_years = sorted(self.years.keys())[-2:]
        recent_years_entries = (
            self.years[two_recent_years[0]] + self.years[two_recent_years[1]]
        )
        most_recent = sorted(recent_years_entries)[-10:]
        most_recent.reverse()
        return most_recent

    def write_overviews(self):
        for info_type in INFO_TYPES:
            if info_type in ["datum", "toegevoegd", "tekst"]:
                continue
            info_items = getattr(self, info_type)
            for info_item in info_items:
                content = []
                title = info_item
                content.append(title)
                content.append("=" * len(title))
                content.append("")
                content.append(".. toctree::")
                content.append("    :maxdepth: 1")
                content.append("")
                sermons = info_items[info_item]
                sermons.sort()
                for sermon in sermons:
                    content.append("    %s" % sermon.tag_link)
                content.append("")
                filename = os.path.join(
                    self.sermonlogdir, INFO_TYPES[info_type].lower(), info_item + ".txt"
                )
                conditional_write(filename, "\n".join(content))


@total_ordering
class Sermon(object):
    """Extracted info from one sermon *.txt file."""

    def __init__(self, year, directory, filename):
        self.year = year
        self.name = filename[:-4]
        self.filename = os.path.join(directory, filename)
        self.lines = utf8_open(self.filename).read().split(u"\n")
        self.title = self.lines[0].strip()
        # Modification time
        self.last_modified = time.gmtime(os.path.getmtime(self.filename))
        self.last_modified = time.strftime("%Y-%m-%dT%H:%M", self.last_modified)
        self.extract_info()

    def __lt__(self, other):
        return self.datum < other.datum

    def __eq__(self, other):
        return self.datum == other.datum

    def extract_info(self):
        for info_type in INFO_TYPES:
            setattr(self, info_type, [])
            tagname = ":%s:" % info_type
            for line in self.lines:
                if tagname in line:
                    info = line.replace(tagname, "")
                    if info_type == "tekst":
                        info_items = info.split(";")
                    else:
                        info_items = info.split(",")
                    info_items = [info_item.strip() for info_item in info_items]
                    setattr(self, info_type, info_items)
                    continue
        if not self.toegevoegd:
            self.add_date_added()
        # For the dates, we don't want lists.
        self.datum = self.datum[0]
        self.toegevoegd = self.toegevoegd[0]

    def add_date_added(self):
        """Add date to lines and write them back.

        Bit of a write-on-read operation, but OK...

        """
        added_on = datetime.date.today().strftime("%Y-%m-%d")
        extra_index = None
        for index, line in enumerate(self.lines):
            if ":datum:" in line:
                extra_index = index
        extra = "   :toegevoegd: %s" % added_on
        if extra_index is None:
            logger.critical(
                ":datum: not found in %s when adding 'toegevoegd' tag.", self.filename
            )
            sys.exit(1)
        self.lines.insert(extra_index, extra)
        utf8_open(self.filename, "w").write("\n".join(self.lines))
        logger.warn(
            "Added 'toegevoegd' tag with value %s to %s", added_on, self.filename
        )
        sys.exit(1)

    @property
    def full_link(self):
        """Return link from the sermonlog homepage."""
        return "%s: %s <%s/%s.txt>" % (self.datum, self.title, self.year, self.name)

    @property
    def tag_link(self):
        """Return link from a tag/church/whatever subdirectory."""
        return "%s: %s <../%s/%s.txt>" % (self.datum, self.title, self.year, self.name)

    @property
    def year_link(self):
        """Return link from the year index page."""
        return "%s: %s <%s.txt>" % (self.datum, self.title, self.name)


def main():
    logging.basicConfig(level=logging.DEBUG)
    if len(sys.argv) < 2:
        print("Missing start dir of weblog")
        sys.exit(1)
    sermonlogdir = sys.argv[1]
    setup_for_plain_docutils()
    sermonlog = Sermonlog(sermonlogdir)
    sermonlog.collect_entries()
    sermonlog.write_years()
    sermonlog.write_index()
    sermonlog.write_overviews()
