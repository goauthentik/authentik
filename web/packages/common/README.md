# @goauthentik/common

The `common` package is a bit of a grab-bag of tools, utilities, and configuration details used
throughout the Authentik front-end suite. Here, we'll try (emphasis on the _try_) to document what
each part does.

-   `./api`

The `./api` folder contains helpers and plug-ins for communicating with the Authentik API. Its
primary purpose is to provide the default configuration details for establishing a channel to the
API, as well as figuring out the default locale, branding information, and even the favicon. (See
what I said about it being a grab-bag?) It has its own list of todos.

-   `/helpers/plex`

Contains configuration tools and access for the Plex TV client. Used by all three primary
interfaces, but again, not exactly a foundational tool.

-   `/helpers/webauthn`

Used entirely by the WebAuthn tools in the Flow interface.

-   `/styles`:

authentik's overrides for patternfly and dark mode.

TODO: Move this into its own package.

-   `/ui`:

Describes the schema of the UIConfig Attributes Object, which dictates certain details about UI
behavior, such as the preliminary state of drawers, editors, and layouts. It also has an API call
to fetch that UIConfig object from the server.

-   `/constants.ts`

Another grab-bag of configuration details: event names, default classnames for setting some visual
details, web socket message type tokens, and the localstorage key.

-   `/enums.ts`

Contains one thing: a mapping of generic UI sizing terms to specific classnames in the CSS.

-   `./errors.ts`

An error handling toolkit related to the `./api` above.

-   `./events.ts`

An extension of the API's "Event" types to assist in reporting server-side events to the user. Has
nothing to do with the browser's internal Event type. Used entirely within `./admin`, may be
suitable to being moved there.

-   `./global.ts`

A single function that retrieves any global information for the UI from the `index.html` file in
which it was invoked. Used by our Django application to preload configuration information.

-   `./labels.ts`,

Maps a variety of API tokens to human-readable labels, including those for:

-   Events
-   Severities
-   User Types
-   Stage Intent

It might make more sense to move these closer to where they're used, if their use is local to a
single interface or component.

-   `./messages.ts`

Contains one thing: a mapping of generic UI alert-level terms to specific classnames in the CSS.

-   `./sentry.ts`

Sentry is an application monitoring package for finding code breakage. The Sentry configuration for
all of our interfaces is kept here.

-   `./users.ts`

Despite the plural name, this is entirely about getting the current user's configuration from the
server. Used by all three major interfaces. Could probably be replaced by a context. (Possibly
already has been.)

-   `./utils.ts`

The classic junk drawer of UI development. A few string functions, a few utilities from
YouMightNotNeedLodash, a slugifier, some date handling utilities, that sort of thing.

-   `./ws.ts`

Sets up our web socket for receiving server-side events. Used by all three major interfaces.
