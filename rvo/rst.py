from docutils import nodes
from docutils.parsers.rst import directives
from docutils.parsers.rst import Directive

SMUGMUG = 'http://photos.reinout.vanrees.org'
TAGLINK = '../../../tags/%s.html'
ROOTTAGLINK = 'tags/%s.html'
SERMONTAGLINK = '../%s.html'


def align(argument):
    """Conversion function for the 'align' option."""
    return directives.choice(argument, ('left', 'center', 'right'))


class TagLinks(Directive):
    separator = ','
    required_arguments = 1
    optional_arguments = 200  # Arbitrary.
    has_content = False
    taglink = TAGLINK
    intro_text = 'Tags: '

    def run(self):
        tags = [arg.replace(self.separator, '') for arg in self.arguments]
        result = nodes.paragraph()
        result['classes'] = ['weblogtags']
        result += nodes.inline(text=self.intro_text)
        count = 0
        for tag in tags:
            count += 1
            link = self.taglink % tag
            tag_node = nodes.reference(refuri=link, text=tag)
            result += tag_node
            if not count == len(tags):
                result += nodes.inline(text='%s ' % self.separator)
        return [result]


class RootTagLinks(TagLinks):
    taglink = ROOTTAGLINK


class SmugmugImage(Directive):

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {'alt': directives.unchanged,
                   'height': directives.nonnegative_int,
                   'width': directives.nonnegative_int,
                   'scale': directives.nonnegative_int,
                   'align': align,
                   }
    # TODO ^^^ size
    has_content = False

    def run(self):
        reference = directives.uri(self.arguments[0])
        if 'gallery/' in reference:
            reference = reference.split('gallery/')[1]
            parts = reference.split('/')
            gallery_id = parts[0]
            photo_id = parts[2]
            if '#' in photo_id:
                photo_id = photo_id.split('#')[0]
            image_url = '%s/photos/%s-M.jpg' % (SMUGMUG, photo_id)
            lightbox = '%s/gallery/%s/1/#%s-A-LB' % (
                SMUGMUG, gallery_id, photo_id)
        else:
            # New style
            if 'A-LB' in reference:
                lightbox = reference
                photo_id = reference.split('#')[1]
                photo_id = photo_id.replace('-A-LB', '')
            else:
                lightbox = reference + '-A-LB'
                photo_id = reference.split('/')[-1]
            image_url = '%s/photos/%s-M.jpg' % (SMUGMUG, photo_id)

        self.options['uri'] = image_url
        image_node = nodes.image(rawsource=self.block_text,
                                 **self.options)
        reference_node = nodes.reference(refuri=lightbox)
        reference_node += image_node
        return [reference_node]


class SermonInfo(Directive):
    required_arguments = 0
    optional_arguments = 0
    option_spec = {'kerk': directives.unchanged,
                   'predikant': directives.unchanged,
                   'tekst': directives.unchanged,
                   'datum': directives.unchanged,
                   'toegevoegd': directives.unchanged,
                   'added': directives.unchanged,
                   'tags': directives.unchanged}
    has_content = False
    taglink = SERMONTAGLINK

    def run(self):
        result = nodes.definition_list()
        for option in sorted(self.options.keys()):
            if option == 'added':
                continue
            term = option.capitalize()
            result += nodes.term(text=term)
            definition = nodes.definition()
            if option in ['kerk', 'predikant', 'tags']:
                value = self.options[option]
                values = [value.strip() for value in value.split(',')]
                paragraph = nodes.paragraph()
                for i, value in enumerate(values):
                    link = SERMONTAGLINK % value
                    paragraph += nodes.reference(refuri=link, text=value)
                    if not i == len(values) - 1:
                        paragraph += nodes.inline(text=', ')
                definition += paragraph
            else:
                paragraph = nodes.paragraph()
                paragraph += nodes.inline(text=self.options[option])
                definition += paragraph
            result += definition
        return [result]


# gallery
# http://photos.reinout.vanrees.org/Vacation/2009-cycling-vechtdalroute/
# 9255700_R2ZDx/1/618290283_v2gri
# lightbox
# http://photos.reinout.vanrees.org/Vacation/2009-cycling-vechtdalroute
# /9255700_R2ZDx/1/#618290283_v2gri-A-LB
# medium img
# http://photos.reinout.vanrees.org/photos/618290283_v2gri-M.jpg


def breadcrumbs(app, pagename, templatename, context, doctree):
    """Inject the main menu into the context

    It is registered for the ``html-page-context`` event.

    """
    master_doc = context['master_doc']
    pathto = context['pathto']
    # env = app.builder.env
    result = []
    result.append({'title': 'Home',
                   'url': pathto(master_doc)})
    if not pagename:
        return
    parts = pagename.split('/')
    ourselves = parts.pop()
    if not parts:
        return
    if ourselves == 'index':
        parts.pop()
    for num in range(len(parts)):
        urlparts = parts[:num + 1] + [master_doc]
        current = '/'.join(urlparts)
        title = parts[num]
        result.append({'title': title,
                       'url': pathto(current)})
    context['breadcrumbs'] = result
    context['breadcrumbs_last'] = context['title']


def _is_weblog_entry(pagename):
    """Return True if the page is a weblog entry."""
    if not pagename:
        return
    parts = pagename.split('/')
    if not parts[0] == 'weblog':
        return
    if not len(parts) == 5:
        return
    if parts[-1] == 'index':
        return
    return True


def enable_disqus(app, pagename, templatename, context, doctree):
    """Inject whether to enable disqus into the context.

    It is registered for the ``html-page-context`` event.

    """
    context['enable_disqus'] = _is_weblog_entry(pagename)


def setup(app):
    """Setup for sphinx"""
    app.add_directive('smugmug', SmugmugImage)
    app.add_directive('tags', TagLinks)
    app.add_directive('roottags', RootTagLinks)

    app.add_directive('preek', SermonInfo)
    app.connect('html-page-context', breadcrumbs)
    app.connect('html-page-context', enable_disqus)


def setup_for_plain_docutils():
    directives.register_directive('smugmug', SmugmugImage)
    directives.register_directive('tags', TagLinks)
    directives.register_directive('roottags', RootTagLinks)
    directives.register_directive('preek', SermonInfo)
