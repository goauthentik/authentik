# Upgrading to 0.10

This upgrade brings a few database changes with it, some of which have to be done manually. The main changes are:

- New OAuth2/OpenID Provider

  This new provider merges both OAuth2 and OpenID. It is based on the codebase of the old provider, which has been simplified and cleaned from the ground up. Support for Property Mappings has also been added. Because of this change, OpenID and OAuth2 Providers will have to be re-created.

- Proxy Provider

  Due to this new OAuth2 Provider, the Application Gateway Provider, now simply called "Proxy Provider" has been revamped as well. The new passbook Proxy integrates more tightly with passbook via the new Outposts system. The new proxy also supports multiple applications per proxy instance, can configure TLS based on passbook Keypairs and more.

- Outpost System

  This is a new Object type, used currently only by the Proxy Provider. It manages the creation and permissions of service accounts, which are used by the outposts to communicate with passbook.

- Flow Import/Export

  Flows can now be imported and exported. This feature can be used as a backup system, or to share complex flows with other people. Example flows have also been added to the documentation to help you get going with passbook.

## Under the hood

- passbook now runs on Django 3.1 and Channels with complete ASGI enabled.
- uwsgi has been replaced with Gunicorn and uvicorn.
- Elastic APM has been replaced with Sentry Performance metrics
- Flow title is now configurable separately from the name
- All logs are now json

## Upgrading

### docker-compose

The docker-compose file has been updated, please download the latest from `https://raw.githubusercontent.com/BeryJu/passbook/master/docker-compose.yml`.
By default, the new compose file uses a fixed version to prevent unintended updates.

Before updating the file, stop all containers. Then download the file, pull the new containers and start the database.

```
docker-compose down
docker-compose pull
docker-compose up --no-start
docker-compose start redis postgrseql
```

To run the commands below, use the prefix `docker-compose run ./manage.py`.

### Helm

A few options have changed:

- `error_reporting` was changed from a simple boolean to a dictionary:

  ```yaml
    error_reporting:
      enabled: false
      environment: customer
      send_pii: false
  ```

- The `apm` and `monitoring` blocks have been removed.
- `serverReplicas` and `workerReplicas` have been added

During this update you must change `serverReplicas` to 0, and run a `helm upgrade`. Otherwise, an automatic upgrade process is attempted.

To run the commands below, use the prefix `kubectl exec -it passbook-*-worker-* -- ./manage.py`.

### Upgrading

For the first few steps, we need an SQL Shell connected to the passbook database. To start this, type in your command prefix from above and ` dbshell`. The entire command should end with this string `[...] ./manage.py dbshell`.

If you are using any OpenID or OAuth2 Providers, you need to export their configuration. Run these commands in the shell that is open.

```
select * from passbook_providers_oauth_oauth2provider ;
select * from oidc_provider_client;
```

After you've copied this information somewhere safe, we can start by cleaning up old tables. Run the command below in the same shell.

```sql
delete from django_migrations where app = 'passbook_stages_prompt';
drop table passbook_stages_prompt_prompt cascade;
drop table passbook_stages_prompt_promptstage cascade;
drop table passbook_stages_prompt_promptstage_fields;
drop table corsheaders_corsmodel cascade;
drop table oauth2_provider_accesstoken cascade;
drop table oauth2_provider_grant cascade;
drop table oauth2_provider_refreshtoken cascade;
drop table oidc_provider_client cascade;
drop table oidc_provider_client_response_types cascade;
drop table oidc_provider_code cascade;
drop table oidc_provider_responsetype cascade;
drop table oidc_provider_rsakey cascade;
drop table oidc_provider_token cascade;
drop table oidc_provider_userconsent cascade;
drop table passbook_providers_app_gw_applicationgatewayprovider cascade;
delete from django_migrations where app = 'passbook_flows' and name = '0008_default_flows';
delete from django_migrations where app = 'passbook_flows' and name = '0009_source_flows';
delete from django_migrations where app = 'passbook_flows' and name = '0010_provider_flows';
delete from django_migrations where app = 'passbook_stages_password' and name = '0002_passwordstage_change_flow';
```

Now that we're done interacting with the database directly, we can exit the shell by typing `\q` and hitting enter.

The next commands should be appended directly to your prefix, and ran in this order. If any of these commands show an error message, please stop and open a GitHub issue.

```
migrate passbook_stages_prompt
migrate passbook_flows 0008_default_flows --fake
migrate passbook_flows 0009_source_flows --fake
migrate passbook_flows 0010_provider_flows --fake
migrate passbook_flows
migrate passbook_stages_password --fake
migrate
```

After all of those commands are done, you can start passbook again, either by running `docker-compose up -d` or changing `serverReplicas` to 1.
