from nose.tools import eq_
import test_utils

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse


class MiddlewareTestCase(test_utils.TestCase):
    """Test our custom middleware(s)."""

    def test_httponly(self):
        uid = 'john'
        pw = 'johnpw'
        User.objects.create_user(uid,'lennon@thebeatles.com', pw)
        r = self.client.post(reverse('cas_login'), {
            'username': uid, 'password': pw})

        # No errors
        eq_(r.status_code, 200)

        # We have cookies and all are httponly unless specified otherwise.
        self.assertTrue(len(r.cookies) > 0)
        for name in r.cookies:
            if name not in settings.JAVASCRIPT_READABLE_COOKIES:
                eq_(bool(r.cookies[name].get('httponly')), True)

    def test_x_frame_options(self):
        """Ensure our pages must not be iframed."""
        r = self.client.get(reverse('cas_login'))
        eq_(r.status_code, 200)
        eq_(r['x-frame-options'], 'DENY')
