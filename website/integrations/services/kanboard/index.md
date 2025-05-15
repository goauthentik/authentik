enable plugin from webui:

1. /var/www/app/config.php add `define('PLUGIN_INSTALLER', true);`
2. locate "OAuth2" plugin and click "Install"
3. nav to click profile in top right > settings > integrations > under OAuth2 Authentication. ui has:
Callback URL kanboard.company/oauth/callback (prefilled)
Client ID
Client Secret
Authorize URL
Token URL
User API URL
Scopes: openid profile email
Username Key: preferred_username
Name Key: name
Email Key: email
User ID Key: sub
toggle Allow Account Creation
click "Save"

test: log out. there's "OAuth2 login" on login page

doc https://github.com/kanboard/plugin-oauth2
