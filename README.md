Secret Squirrel
===============

Secret Squirrel is a [Django][Django]-based [Single Sign-on][SSO] server. It
uses [CAS][CAS] (version 1) as the client-side protocol and can be used with
any [CAS client library][CAS-libs].

Secret Squirrel is a [Mozilla][Mozilla] project and published under a BSD
license.

[Django]: http://www.djangoproject.com/
[SSO]: http://en.wikipedia.org/wiki/Single_sign-on
[CAS]: http://en.wikipedia.org/wiki/Central_Authentication_Service
[CAS-libs]: http://www.ja-sig.org/wiki/display/CASC
[Mozilla]: http://www.mozilla.org

Getting Started
---------------
### Python
You need Python 2.6. Also, you probably want to run this application in a
[virtualenv][virtualenv] environment.

Run ``easy_install pip`` followed by ``pip install -r requirements/prod.txt``
to install the required Python libraries.

[virtualenv]: http://pypi.python.org/pypi/virtualenv

### Django
The Internet has plenty of of documentation on setting up a Django application
with any web server. If you need a wsgi entry point, you can find one in
``wsgi/squirrel.wsgi``.

### Whitelist
For each website which you want to SSO enable, you'll need to add them to the
whitelist.

1. ``http://localhost:8001/admin``

   Login with admin user

2. Client Sites > Click Add 

   *Note:* Don't confuse [Sites][DjangoSites] (i.e., the Django Sites framework)
   with "Client Sites" (i.e., the SSO Whitelist)... They have very similar
   inputs and similar names.

[DjangoSites]: http://docs.djangoproject.com/en/dev/ref/contrib/sites/

3. Enter Details

    *Example:* 
    Name: ``PHP Example App``
    Domain: ``phpclient.secretsquirr.el``
    Match priority: ``0``

    Click Save
