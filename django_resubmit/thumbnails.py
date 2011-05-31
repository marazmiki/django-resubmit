import mimetypes
import Image


from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.db.models.fields.files import FieldFile
from django.utils.encoding import iri_to_uri
from sorl.thumbnail.templatetags.thumbnail import PROCESSORS
from sorl.thumbnail.main import DjangoThumbnail

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class ThumbFabrica(object):
    def __init__(self, value, widget):
        self.value = value
        self.widget = widget

    def thumb(self):
        guess_type = self.guess_type()
        if guess_type in ['image/png', 'image/jpeg', 'image/gif']:
            return ImageThumb(self.value, self.widget)
        elif guess_type in ['video/mpeg', 'video/quicktime']:
            pass # return VideoThumb(self.value, self.size) 

    def guess_type(self):
        if isinstance(self.value, InMemoryUploadedFile):
            return self.value.content_type
        elif isinstance(self.value, FieldFile):
            guess_types = mimetypes.guess_type(self.value.file.name)
            if guess_types and isinstance(guess_types, tuple):
                return guess_types[0]


class ImageThumb(object):
    def __init__(self, value, widget):
        self.value = value
        self.widget = widget

    def _memory(self, upload):
        """ Return image thumbnail as SimpleUploadedFile (subclass of InMemoryUploadedFile) """
        upload.file.seek(0)
        img = Image.open(upload.file)
        img.thumbnail(self.widget.thumb_size, Image.ANTIALIAS)
        buf = StringIO()
        img.save(buf, img.format)
        buf.seek(0)
        thumb = SimpleUploadedFile(upload.name, buf.read(), upload.content_type)
        buf.close()
        return thumb

    def _filesystem(self, value):
        """ Make real filesystem thumbnail and return url"""
        image_path = iri_to_uri(value)
        t = DjangoThumbnail(relative_source=image_path,
                            requested_size=self.widget.thumb_size,
                            processors=PROCESSORS)
        return t.absolute_url

    def _src(self):
        """ Get SRC attribute for HTML tag IMG"""
        if type(self.value) == InMemoryUploadedFile:
            thumbnail_url = reverse('django_resubmit.views.thumbnail')
            return thumbnail_url + "?key=%s&name=%s&width=%s&height=%s" % (self.widget.hidden_key, self.value.name, self.widget.thumb_size[0], self.widget.thumb_size[1])
        elif type(self.value) == FieldFile:
            return self._filesystem(self.value)

    def render(self):
        """ Render thumbnail """
        html = '';
        src = self._src()
        if src:
            html += """<img alt="preview" src="%s" /> """ % src
        return html
