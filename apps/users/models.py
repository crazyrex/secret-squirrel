from datetime import datetime
import hashlib
import random
import re
import string
import time

from django.conf import settings
from django.contrib.auth.models import User as DjangoUser
from django.core.mail import send_mail
from django.db import models
from django.template import Context, loader

from sso.urlresolvers import reverse

import commonware.log
from tower import ugettext as _

log = commonware.log.getLogger('sso.users')


def get_hexdigest(algorithm, salt, raw_password):
    return hashlib.new(algorithm, salt + raw_password).hexdigest()


def rand_string(length):
    return ''.join(random.choice(string.letters) for i in xrange(length))


def create_password(algorithm, raw_password):
    salt = get_hexdigest(algorithm, rand_string(12), rand_string(12))[:64]
    hsh = get_hexdigest(algorithm, salt, raw_password)
    return '$'.join([algorithm, salt, hsh])

def authenticate(username=None, password=None):
    try:
        user_profile = UserProfile.objects.get(user__username=username)
        if user_profile.check_password(password):
            return user_profile.user
    except UserProfile.DoesNotExist:
        return None

class UserProfile(models.Model):
    # RFC 4122 UUID. Never changes. Used by client apps
    sso_uuid = models.CharField(max_length=36, blank=True)
    nickname = models.CharField(max_length=255, unique=True, default='',
                                null=True, blank=True)
    firstname = models.CharField(max_length=255, default='', blank=True)
    lastname = models.CharField(max_length=255, default='', blank=True)
    password = models.CharField(max_length=255, default='')
    email = models.EmailField(unique=True)

    confirmationcode = models.CharField(max_length=255, default='',
                                        blank=True)

    deleted = models.BooleanField(default=False)
    resetcode = models.CharField(max_length=255, default='', blank=True)
    resetcode_expires = models.DateTimeField(default=datetime.now, null=True,
                                             blank=True)

    user = models.ForeignKey(DjangoUser, null=True, editable=False, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'

    def __unicode__(self):
        return '%s: %s' % (self.id, self.display_name)

    @property
    def display_name(self):
        if not self.nickname:
            return '%s %s' % (self.firstname, self.lastname)
        else:
            return self.nickname

    @property
    def welcome_name(self):
        if self.firstname:
            return self.firstname
        elif self.nickname:
            return self.nickname
        elif self.lastname:
            return self.lastname

        return ''

    def anonymize(self):
        log.info("User (%s: <%s>) is being anonymized." % (self, self.email))
        self.email = ""
        self.password = "sha512$Anonymous$Password"
        self.firstname = ""
        self.lastname = ""
        self.nickname = None
        self.deleted = True
        self.save()

    def save(self, force_insert=False, force_update=False, using=None):
        # we have to fix stupid things that we defined poorly in remora
        if self.resetcode_expires is None:
            self.resetcode_expires = datetime.now()

        super(UserProfile, self).save(force_insert, force_update, using)

    def check_password(self, raw_password):
        if '$' not in self.password:
            valid = (get_hexdigest('md5', '', raw_password) == self.password)
            if valid:
                # Upgrade an old password.
                self.set_password(raw_password)
                self.save()
            return valid

        algo, salt, hsh = self.password.split('$')
        return hsh == get_hexdigest(algo, salt, raw_password)

    def set_password(self, raw_password, algorithm='sha512'):
        self.password = create_password(algorithm, raw_password)

    def email_confirmation_code(self):
        url = "%s%s" % (settings.SITE_URL,
                        reverse('users.confirm',
                                args=[self.id, self.confirmationcode]))
        domain = settings.DOMAIN
        t = loader.get_template('users/email/confirm.ltxt')
        c = {'domain': domain, 'url': url, }
        send_mail(_("Please confirm your email address"),
                  t.render(Context(c)), None, [self.email])

    def create_django_user(self):
        """Make a django.contrib.auth.User for this UserProfile."""
        # Reusing the id will make our life easier, because we can use the
        # OneToOneField as pk for Profile linked back to the auth.user
        # in the future.
        self.user = DjangoUser(id=self.pk)
        self.user.first_name = self.firstname
        self.user.last_name = self.lastname
        self.user.username = self.email
        self.user.email = self.email
        self.user.password = self.password
        self.user.date_joined = self.created

        self.user.save()
        self.save()
        return self.user


class BlacklistedNickname(models.Model):
    """Blacklisted user nicknames."""
    nickname = models.CharField(max_length=255, unique=True, default='')

    def __unicode__(self):
        return self.nickname

    @classmethod
    def blocked(cls, nick):
        """Check to see if a nickname is in the blacklist."""
        # Could also cache the entire blacklist and simply check if the
        # nickname is in the list here. @TODO?
        return cls.objects.only('nickname').filter(nickname=nick).exists()
