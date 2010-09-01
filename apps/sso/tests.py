from nose.tools import eq_
import test_utils

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse


class MiddlewareTestCase(test_utils.TestCase):
    """Test our custom middleware(s)."""
    def _login(self):
        """Create a new user and log them in."""
        uid = 'john'
        pw = 'johnpw'
        User.objects.create_user(uid,'lennon@thebeatles.com', pw)
        self.client.login(username=uid, password=pw)

    def test_httponly(self):
        self._login()

        r = self.client.get(reverse('cas_login'))

        # No errors, and we are logged in
        eq_(r.status_code, 302)

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

    def test_session_ip_check(self):
        """Make sure our session cookies are tied to a single IP."""
        different_forwarded_for = '192.168.0.1, 192.168.0.2'

        self._login()

        r = self.client.get(reverse('home'))
        self.assertTrue(r.context['user'].is_authenticated())

        r = self.client.get(reverse('home'),
                            HTTP_X_FORWARDED_FOR=different_forwarded_for)
        self.assertFalse(r.context['user'].is_authenticated())
