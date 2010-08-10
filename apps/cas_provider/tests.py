from datetime import datetime

from mock import patch
from nose.tools import eq_
import test_utils

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from .models import ServiceTicket


class ValidateTestCase(test_utils.TestCase):
    """Test ticket validation."""

    @patch('cas_provider.models.ServiceTicket.objects.get')
    def test_expired_ticket(self, mock):
        """Do not allow validation of expired tickets."""
        mock.side_effect = self._expired_ticket
        r = self.client.get(
            '%s?service=abc&ticket=def' % reverse('cas_validate'))
        eq_(r.content.find('no'), 0)

    def _expired_ticket(self, *args, **kwargs):
        """Generate an expired service ticket."""
        st = ServiceTicket(user=User())
        st.created = datetime(2010, 1, 1)
        st.delete = lambda: None
        return st
