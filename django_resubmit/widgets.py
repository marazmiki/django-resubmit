# coding: utf-8
from __future__ import absolute_import

from django.contrib.admin.widgets import AdminFileWidget
from django.core.urlresolvers import reverse
from django.forms.widgets import Input
from django.forms.widgets import CheckboxInput
from django.forms.widgets import HiddenInput
from django.forms.widgets import FILE_INPUT_CONTRADICTION
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils.encoding import force_unicode

from .conf import settings
from .storage import get_default_storage


FILE_INPUT_CLEAR = False


class FileWidget(AdminFileWidget):

    class Media:
        css = {'all': (settings.STATIC_URL + 'django_resubmit/widget.css',)}
        js = (#'https://raw.github.com/malsup/form/master/jquery.form.js',
              settings.STATIC_URL + 'django_resubmit/jquery.form.js',
              settings.STATIC_URL + 'django_resubmit/widget.js',)

    def __init__(self, *args, **kwargs):
        self.thumb_size = settings.RESUBMIT_THUMBNAIL_SIZE
        self.set_storage(get_default_storage())
        self.hidden_key = u""
        self.isSaved = False
        super(FileWidget, self).__init__(*args, **kwargs)

    def value_from_datadict(self, data, files, name):
        self.hidden_key = data.get(self._hidden_keyname(name), "")

        upload = super(FileWidget, self).value_from_datadict(data, files, name)

        # user checks 'clear' or checks 'clear' and uploads a file
        if upload is FILE_INPUT_CLEAR or upload is FILE_INPUT_CONTRADICTION:
            if self.hidden_key:
                self._storage.clear_file(self.hidden_key)
                self.hidden_key = u""
            return upload

        if files and name in files:
            if self.hidden_key:
                self._storage.clear_file(self.hidden_key)
            upload = files[name]
            self.hidden_key = self._storage.put_file(upload)
        elif self.hidden_key:
            restored = self._storage.get_file(self.hidden_key, name)
            if restored:
                upload = restored
                files[name] = upload
            else:
                self.hidden_key = u""

        return upload

    def render(self, name, value, attrs=None):
        default_attrs = {'class':'resubmit'}
        attrs = attrs or {}
        attrs.update(default_attrs)
        substitutions = {
            'input': Input().render(name, None, self.build_attrs(attrs, type=self.input_type)),
            'input_text': self.input_text,
            'initial_text': self.initial_text,
            'clear_template': '',
            'clear_checkbox_label': self.clear_checkbox_label,
        }
        template = u'%(input)s'

        if value and hasattr(value, "url"):
            template = self.template_with_initial
            substitutions['initial'] = (u'<a target="_blank" href="%s">%s</a>' % (escape(value.url), escape(force_unicode(value))))
        elif self.hidden_key:
            template = self.template_with_initial
            substitutions['initial'] = escape(force_unicode(value.name))

        if not self.is_required and value and (hasattr(value, "url") or self.hidden_key):
            checkbox_name = self.clear_checkbox_name(name)
            checkbox_id = self.clear_checkbox_id(checkbox_name)
            substitutions['clear_checkbox_name'] = checkbox_name
            substitutions['clear_checkbox_id'] = checkbox_id
            substitutions['clear'] = CheckboxInput().render(checkbox_name, False, attrs={'id': checkbox_id})
            substitutions['clear_template'] = self.template_with_clear % substitutions

        width, height = self.thumb_size
        substitutions['input'] += (HiddenInput().render(self._hidden_keyname(name), self.hidden_key or '', {}) +
                u'<span class="resubmit-preview" style="width: %(max_width)dpx; height: %(max_height)dpx" >'
                u'<img alt="preview" style="max-width: %(max_width)dpx; max-height: %(max_height)dpx" %(src)s class="resubmit-preview__image" />'
                u'</span>' % dict(
                    max_width = width,
                    max_height = height,
                    src = 'src="%s"' % (reverse('django_resubmit:preview', args=[self.hidden_key]) if self.hidden_key else value.url if value else  u''))
                )
        return mark_safe(template % substitutions)

    def _hidden_keyname(self, name):
        return "%s-cachekey" % name

    def set_storage(self, value):
        self._storage = value

