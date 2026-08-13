import { createContext } from "@lit/context";

/**
 * The absolute mount path a routed tab group lives under, e.g.
 * `/if/user/settings`.
 *
 * The router's outlet provides it for the current page; each `<ak-tabs routed>`
 * consumes it as its base and, in turn, provides its active panel's path to its
 * own subtree — so a nested tab group derives its base with no page wiring. A
 * dispatcher page (provider/source/connector view) is transparent to this: the
 * value flows through it to the type-specific view's tabs.
 */
export const routedTabBaseContext = createContext<string>(Symbol("authentik-routed-tab-base"));
