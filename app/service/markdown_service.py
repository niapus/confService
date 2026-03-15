import markdown
# from markdown.extensions import extra
# from markdown.extensions.extra import extensions
# from markdown.extensions.toc import TocExtension
# from markdown.extensions.codehilite import CodeHiliteExtension
import bleach

class MarkdownService:
    def __init__(self):
        self.__extensions = [
            'extra',
            'codehilite',
            'toc',
        ]

        self.__extensions_config = {
            'toc': {
                'permalink': False,
                'toc_class': 'table-of-contents'
            }
        }

        self.__md = markdown.Markdown(
            extensions=self.__extensions,
            extension_configs=self.__extensions_config
        )

    def to_html(self, md_text):
        html = self.__md.reset().convert(md_text)
        return self.__secure_html(html)

    def __secure_html(self, html):
        allowed_tags = [
            'p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'strong', 'em', 'u', 's', 'mark',
            'ul', 'ol', 'li', 'dl', 'dt', 'dd',
            'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'pre', 'code', 'blockquote',
            'a', 'img',
            'div', 'span', 'hr',
        ]

        allowed_attrs = {
            '*': ['class'],
            'a': ['href', 'title', 'target'],
            'img': ['src', 'alt', 'title'],
            'td': ['colspan', 'rowspan'],
        }

        return bleach.clean(
            html,
            tags=allowed_tags,
            attributes=allowed_attrs
        )