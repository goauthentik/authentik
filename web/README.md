# The authentik WebUI

The authetik WebUI is the default UI for the authentik Single Sign-on (SSO) server. It consists of
three primary applications:

- Flow: The transaction-driven interface for logging in and other activities
- User: The user's library of applications to which they have access, and some user settings
- Admin: The system adminstration tool for defining applications, providers, policies, and
  everything else
  
Each of these is a [thin client][] around data objects provided by and transactions available with
the authentik SSO server.

The authentik SSO server is written in Python and Django.

> - [thin client](https://en.wikipedia.org/wiki/Thin_client): In this case, we mean "a front end to
>  show the data where the serve does all the heavy lifting."

## Project setup

If you have cloned the authentik repository, the [developer docs] are where you go to perform the
initial set-up and install. This sequence will get you up and running in the usual course of events.

```
$ make install
$ make gen-dev-config
$ make migrate
$ make run-server
$ make run-worker
```

We recommend that you run `run-server` and `run-worker` in different terminals or different sessions
under tmux or screen or a similar terminal multiplexer.

The WebUI runs in this folder (`./web` under the project root).  You can put the WebUI into hot
reload by running, from this folder,

```
$ npm run watch
```

## WebUI Architecture

### The Django side

The WebUI is delivered via a Django server.  The server delivers an HTML template that executes a
sequence of startup operations:

- Assigns the language code and `data-theme="light|dark"` settings to the `html` tag. Assigns the
  favicon links. Creates a `window.authentik` object and assigns a variety of site-wide
  configuration details to it. Probes the a priority decision list of sources of the user's
  light/dark preferences and assigns that to the `Document.dataset`
- Begins loading the interface root bundle. The script is of `type="module"`; it will not be
  executed until the initial HTML has been completely parsed.
- Loads the site-wide standard CSS.
- Injects any CSS overrides specified in the customer's `brand` settings
- Loads any necessary JavaScript polyfills
- Dispatches any initial messages to the notification handler
- Sets any custom `<meta>` settings specified by the server
- Provides the initial HTML scaffolding to launch an interface.

The interface code is mostly the core web component and its responsibilities.  This code will be
hydrated when the interface root bundle in the second step above is executed and the components are
registered with the browser.

### The Flow Interface

The Flow Interface has three subsystems:

- The Locale Selector: `<ak-locale-select>`
- The Flow Inspector: `<ak-flow-inspector>`
- The Flow Executor: `<ak-flow-executor>`

The Locale Selector and the Inspector are independent buttons that exist on the page (both can
be disabled by admin preference). The Locale Selector does exactly that. The Flow Inspector, when
enabled, can query the server for details about the state of a flow: the accumulated context of the
current flow, existing error messages, and expected next steps; it is present to assist with
debugging.

The Executor is the heart of the system. It executes Flows.

A *Flow* in authentik is the workflow that accomplishes a specific SSO-oriented task such as logging
in, logging out, or enrolling as a new user, among other tasks.

The Executor starts by examining the current URL for the `flowSlug`, and sends a request for a
*Challenge* to the server. Upon the response, the Executor loads the corresponding *Stage*: the UI
component responsible for showing the challenge to the user. When the user performs the requested
action the input is sent to the server, which issues a new Challenge. This Challenge may be the same
one with error messages, or the next one in the workflow. This process repeats until the user
reaches the end of the Flow, at which point the task is complete or failed.

The architecture for the Executor is straightforward:

- The HTML Document
  - The Locale Selector
  - The Inspector
  - The Executor
    - The current Stage

A Stage may have interior stages or components. The Identification Stage is the most complex of our
stages. It usually shows the Username field, and it *may* host the password; in that case, the
password component exists to allow the user to "show password". It may also host the Captcha and
Passkey stages within, to complete the initial user identity and validity.

### User and Admin Interfaces

The architecture of these interfaces is more complex.  In both cases, the user is assumed to have
logged in and so is said to have a *Session*.  The architecture is structured:

- The HTML Document
- The Interface
  - Licence: a context handler for the site's enterprise license status
  - Session: a context handler for the user's current session.  This mostly the `user` identity
  - Version: a context handler for the current version of authentik
  - Notifications: a context handler for outstanding messages sent from the server to the user
  - Capabilities: a list of features that the current user may use.  List includes "can save
    reports," "can use debugging feature," "can use enterprise features."
  - The Application:
    - Header
    - Sidebar
    - Router
      - CRUD interfaces to features of the system:
        - Dashboard
        - Logs
        - Configurations
          - Flows, Stages & Policies
          - Users & Group
          - IDP Sources
          - Everything else!

### Miscellaneous Interfaces

There are three miscellaneous interfaces:

#### API Browser

A single page app that loads our schema and allows the user to experiment with it.  Uses the
[RapiDoc](https://rapidocweb.com/) app.

#### Loading

The Django application is wrapped in a proxy server for caching and performance; while it is in
start-up mode, the proxy serves this page, which just says "The application is loading" with a
pretty animation.

#### SFE: Simplified Flow Executor

The SFE is a limited version of the FlowExecutor written to use [jQuery](https://jquery.com/). It
supports only log-in operations, and is meant for places where the log-in is embedded in an
Office365 or MicrosoftTeams settings, as those use Trident (Internet Explorer) for their web-based
log-in.

## WebUI Foundations

### CSS

Our current CSS is provided by [Patternfly 4](https://v4-archive.patternfly.org/v4/).  There are two
different layers of CSS.

The first is the Global CSS that appears in the `<head>`.  This defines the basic look: theme,
start-up, reset, and fonts.  It also provides the CSS Custom Properties that will control the look
and feel of the rest of an Interface.

The second is per-component CSS. This is linked into each component using [Adopted
Stylesheets](https://developer.mozilla.org/en-US/docs/Web/API/Document/adoptedStyleSheets).

> This recipe has led to some significant awkwardness. Information from the outside does not pierce
> the shadowDOM, so Patternfly-Base is linked into every component just to provide the box model,
> reset, basic functionality, and behavioral modifiers. The interior of our components is cluttered
> with lots of patternfly classes.

### Elements

Elements are custom web components that authentik has written that supply advanced behaviors to
common operations, as well as API-independent complex components such as rich drop-downs, dual-pane
selectors, toggles, switches, and wizards.  At least, that's the idea.  We are still untangling.

### Components

Components are custom web components that authentik has written that are API-aware and that supply
business logic to perform validation, permissioning, and selective display.

## Adding a new feature (developer's guide)

As a thin client, the primary task will either be adding a new CRUD vertical or extending and
enhancing an existing one. (If the elements, components, API, and so on represent the horizontal
layers of an application, a single CRUD task is the "vertical slice" through these.) Our Django
application presents collections of objects from which the user may pick one to view, update, or
delete.

The web component in `./elements/table` is used to display, well, tables of components. A new
feature begins by inheriting the `Table` class and providing two things: the API call to retrieve
the objects, and a method describing a row for the table. This is the retrieval for our Role-Based
Access Controls (RBAC).

```
    async apiEndpoint(): Promise<PaginatedResponse<Role>> {
        return new RbacApi(DEFAULT_CONFIG).rbacRolesList({
            ...(await this.defaultEndpointConfig()),
            managedIsnull: this.hideManaged ? true : undefined,
        });
    }

```

The complete list of APIs available can be found in `node_modules/@goauthentik/api/src/apis`.

A row returns an array of cells:

```
    row(item: Role): SlottedTemplateResult[] {
        return [
            html`<a href="#/identity/roles/${item.pk}">${item.name}</a>`,
            html`<div>
                <ak-forms-modal>
                    <span slot="submit">${msg("Update")}</span>
                    <span slot="header">${msg("Update Role")}</span>
                    <ak-role-form slot="form" .instancePk=${item.pk}> </ak-role-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
            </div>`,
        ];
    }

```

This example shows the use of the `modal` dialogue to show the "update role" form.  Deciding to use
a modal or to move to a different page is a matter of taste, but mostly rests on how large the form
is. If it's likely to have internal scrolling, opt for a separate page.

For complex objects that have a lot of detail or subsidiary lists of features (such as Flows),
provide a separate View page for each one.  We have a specified display standard encapsulated in our
DictionaryList component.

Creation and Updating are handled using the web component parent in `./elements/forms`.  Like
tables, a child component inherits and extends the Form class, providing three features: how to
*retrieve* the object, how to *send* the object, and what to ask for. (RBAC is small enough, it's
useful as an example):

```
    loadInstance(pk: string): Promise<Role> {
        return new RbacApi(DEFAULT_CONFIG).rbacRolesRetrieve({
            uuid: pk,
        });
    }

    async send(data: Role): Promise<Role> {
        if (this.instance?.pk) {
            return new RbacApi(DEFAULT_CONFIG).rbacRolesPartialUpdate({
                uuid: this.instance.pk,
                patchedRoleRequest: data,
            });
        }
        return new RbacApi(DEFAULT_CONFIG).rbacRolesCreate({
            roleRequest: data,
        });
    }
    
    protected override renderForm(): TemplateResult {
        return html`<ak-form-element-horizontal label=${msg("Name")} required name="name">
            <input
                type="text"
                value="${ifDefined(this.instance?.name)}"
                class="pf-c-form-control"
                required
            />
        </ak-form-element-horizontal>`;
    }

```

The `send` shows two different modes: If the existing instance has an identity, this is an update;
otherwise it's a creation request.

These are *simple* examples, naturally, and our application can get much more complicated.  The
`./admin/flows` vertical is one of the most complex, including:

- A per-flow view page with a [Mermaid](https://mermaid.js.org/) diagram to show a Flow's Stages
- A sub-table of the Flow's Policies, with the ability to edit each Policy or its Bindings
- A sub-table of the Flow's Stages with the ability to edit each Stage or a Stage's Binding directly
- A sub-table of the Flow's Permissions

## Choosing To Use A Custom Component (developer's guide)

Some of our server-side objects come with lists.  When editing a list, we suggest:

- If it's a simple list and there's only one choice, use `<select>`
- If it's from the server and it's possible there are more than 100 items, use SearchSelect. It
  has features for showing complex list objects and narrowing down search items.
- If the user can select multiple choices, use DualSelect

### License

This code is licensed under the [MIT License](https://www.tldrlegal.com/license/mit-license).
[A copy of the license](./LICENSE.txt) is included with this project.
