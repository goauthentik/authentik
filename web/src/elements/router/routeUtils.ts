import { Route, RouteArgs } from "@goauthentik/elements/router/Route";
import { P, match } from "ts-pattern";

import { TemplateResult } from "lit";

type ListRoute = () => Promise<TemplateResult<1>>;
type ViewRoute = (_1: RouteArgs) => Promise<TemplateResult<1>>;
type InternalRedirect = string;
type ExternalRedirect = [string, boolean];

type RouteInvoke = ViewRoute | ListRoute;

type RedirectRoute = [string, InternalRedirect | ExternalRedirect];
type PageRoute = [string, RouteInvoke];

export type RawRoute = PageRoute | RedirectRoute;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const isLoader = (v: any): v is RouteInvoke => typeof v === "function";

// When discriminating between redirects and loaders, the loader type is irrelevant to routing
// correctly. The loader type *is* still well-typed to prevent an incompatible loader being added to
// a route, but the two different loader types-- ones that take arguments, and ones that do not-- do
// not matter to the route builder.

// On the other hand, the two different kinds of redirects *do* matter, but only because JavaScript
// makes a distinction between methods of one argument that can be `call`'ed and methods of more
// than one argument that must be `apply`'d. (Spread arguments are converted to call or apply as
// needed).

// prettier-ignore
export function makeRoute(route: RawRoute): Route {
    return match(route)
        .with([P.string, P.when(isLoader)],
              ([path, loader]) => new Route(new RegExp(path), loader))
        .with([P.string, P.string],
              ([path, redirect]) => new Route(new RegExp(path)).redirect(redirect))
        .with([P.string, [P.string, P.boolean]],
              ([path, redirect]) => new Route(new RegExp(path)).redirect(...redirect))
        .exhaustive();
}
