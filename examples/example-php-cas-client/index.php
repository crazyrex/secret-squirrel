<?php
/* ***** */
// import phpCAS lib
set_include_path(get_include_path() . PATH_SEPARATOR . dirname(__FILE__).'/CAS'); 
include_once('CAS.php');

phpCAS::setDebug();

// initialize phpCAS
phpCAS::client(CAS_VERSION_1_0, 'localhost', 8001, 'users');

// no SSL validation for the CAS server
phpCAS::setNoCasServerValidation();
/* ***** */

if (isset($_REQUEST['login'])) {
    // force CAS authentication
    phpCAS::forceAuthentication();

    // at this step, the user has been authenticated by the CAS server
    // and the user's login name can be read with phpCAS::getUser().
    $user = phpCAS::getUser();
    $ver = phpCAS::getVersion();
    render(<<<EOT
    <h1>Successful Authentication!</h1>
    <p>the user's login is $user</b>.</p>
    <p>the phpCAS version is $ver</b>.</p>
    <p><a href="?logout=">Log out</a></p>
EOT
);

} elseif (isset($_REQUEST['logout'])) {
    // logout if desired
    phpCAS::logout();

} else {
    render(<<<EOT
    <h1>Welcome!</h1>
    <p><a href="?login=">Click here to log in via SSO</a></p>
EOT
);
}

function render($content) {
    print <<<EOT
<html>
  <head>
    <title>phpCAS simple client</title>
  </head>
  <body>
    $content
  </body>
</html>
EOT;
}

