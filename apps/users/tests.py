from nose.tools import eq_
import test_utils

from django.contrib.auth.models import User

from . import auth


class AuthTestCase(test_utils.TestCase):
    """Test our patched auth backend."""

    def test_sha256(self):
        """Ensure we use SHA256 consistently as our PW hash."""
        uid = 'john'
        pw = 'johnpw'
        user = User.objects.create_user(uid, 'lennon@thebeatles.com', pw)
        loggedin = self.client.login(username=uid, password=pw)
        self.assertTrue(loggedin)

        # Analyze stored PW field.
        algo, salt, hexdigest = user.password.split('$')
        eq_(algo, 'sha256')
        eq_(len(salt), 10)  # We use a ten-digit salt.
        eq_(len(hexdigest), 64)  # SHA256 hashes are 64 hex chars long.
