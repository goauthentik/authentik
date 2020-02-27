# Expression Policy

Expression Policies allows you to write custom Policy Logic using Jinja2 Templating language.

For a language reference, see [here](https://jinja.palletsprojects.com/en/2.11.x/templates/).

The following objects are passed into the variable:

- `request`: A PolicyRequest object, which has the following properties:
    - `request.user`: The current User, which the Policy is applied against. ([ref](../../property-mappings/reference/user-object.md))
    - `request.http_request`: The Django HTTP Request, as documented [here](https://docs.djangoproject.com/en/3.0/ref/request-response/#httprequest-objects).
    - `request.obj`: A Django Model instance. This is only set if the Policy is ran against an object.
- `pb_is_sso_flow`: Boolean which is true if request was initiated by authenticating through an external Provider.
- `pb_is_group_member(user, group_name)`: Function which checks if `user` is member of a Group with Name `gorup_name`.
- `pb_logger`: Standard Python Logger Object, which can be used to debug expressions.
- `pb_client_ip`: Client's IP Address.

There are also the following custom filters available:

- `regex_match(regex)`: Return True if value matches `regex`
- `regex_replace(regex, repl)`: Replace string matched by `regex` with `repl`
