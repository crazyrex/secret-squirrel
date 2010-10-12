from uuid import uuid4

from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


class UserProfile(models.Model):
    """
    Provides a place for 1:1 attributes that are associated with a SSO user.

    The sso_uuid is a RFC 4122 style UUID which is assigned at object creation.
    It is the only ID which a client SSO application should use. Email,
    username, etc are not guaranteed to be stable.

    Access via get_profile() method on a User object.
    """
    user = models.OneToOneField(User)
    sso_uuid = models.CharField(_('UUID'), max_length=36, default=str(uuid4()))

def user_saved(sender, **kwargs):
    """After a new user is saved in the db we should create their profile."""
    if User == sender:
        if 'created' in kwargs and kwargs['created']:
            profile = UserProfile(user=kwargs['instance'])
            profile.save()

post_save.connect(user_saved)
