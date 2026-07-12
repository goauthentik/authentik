/**
 * @file History-API navigation and document-level click interception.
 *
 * `navigate` drives the history API. `createClickInterceptor` returns a
 * capture-phase click handler that claims a click **only** when it can
 * confidently resolve it to an in-interface path navigation; every other click
 * falls through to the browser. The failure mode is always a full page load,
 * never a dead click.
 *
 * Written so the Navigation API can replace the history source later without
 * touching route tables or outlets.
 */

export type NavigationMode = "push" | "replace" | "assign";

export interface NavigateOptions {
    mode?: NavigationMode;
}

/**
 * Dispatched on `window` after a same-document navigation, so the outlet can
 * re-match without waiting for `popstate` (which the history API does not fire
 * for programmatic pushes).
 */
export class RouterNavigateEvent extends Event {
    static readonly eventName = "ak-router-navigate";

    constructor() {
        super(RouterNavigateEvent.eventName, { bubbles: true, composed: true });
    }
}

declare global {
    interface WindowEventMap {
        [RouterNavigateEvent.eventName]: RouterNavigateEvent;
    }
}

/**
 * Navigate to a destination.
 *
 * @param to An absolute or relative URL. Relative URLs resolve against the
 * current origin.
 * @param options `mode` selects `pushState` (default), `replaceState`, or a
 * full-page `location.assign`.
 */
export function navigate(to: string | URL, { mode = "push" }: NavigateOptions = {}): void {
    const url = to instanceof URL ? to : new URL(to, window.location.origin);

    if (mode === "assign") {
        window.location.assign(url.href);
        return;
    }

    if (url.href === window.location.href) return;

    if (mode === "replace") {
        history.replaceState(null, "", url.href);
    } else {
        history.pushState(null, "", url.href);
    }

    window.dispatchEvent(new RouterNavigateEvent());
}

//#region Click interception

export interface AnchorClickContext {
    button: number;
    metaKey: boolean;
    ctrlKey: boolean;
    shiftKey: boolean;
    altKey: boolean;
    defaultPrevented: boolean;
    /**
     * The anchor's `target` attribute, if any.
     */
    target: string | null;
    /**
     * Whether the anchor carries a `download` attribute.
     */
    hasDownload: boolean;
    /**
     * The anchor's resolved absolute `href`, if any.
     */
    href: string | null;
}

export interface InterceptScope {
    /**
     * The current document origin, e.g. `https://id.example.com`.
     */
    origin: string;
    /**
     * Deployment base path, trailing-slashed.
     */
    base: string;
    /**
     * Interface prefix segment.
     */
    interfaceName: string;
    /**
     * The current `location.pathname`.
     */
    currentPathname: string;
    /**
     * The current `location.search`, with a leading `?` or an empty string.
     */
    currentSearch: string;
}

/**
 * Decide whether a click should be claimed for in-app navigation.
 *
 * @returns the resolved in-interface URL to navigate to, or `null` to let the
 * browser handle the click.
 */
export function decideInterception(ctx: AnchorClickContext, scope: InterceptScope): URL | null {
    if (ctx.defaultPrevented) return null;
    if (ctx.button !== 0) return null;
    if (ctx.metaKey || ctx.ctrlKey || ctx.shiftKey || ctx.altKey) return null;
    if (ctx.hasDownload) return null;
    if (ctx.target && ctx.target !== "_self") return null;
    if (!ctx.href) return null;

    let url: URL;

    try {
        url = new URL(ctx.href, scope.origin);
    } catch {
        return null;
    }

    if (url.origin !== scope.origin) return null;

    // A URL that matches the current path and query differs at most by fragment
    // (`#section`), or is identical/empty (native reload). Either way the
    // browser owns it: claiming would suppress the native fragment scroll.
    if (url.pathname === scope.currentPathname && url.search === scope.currentSearch) return null;

    const base = scope.base.endsWith("/") ? scope.base : `${scope.base}/`;
    const prefix = `${base}if/${scope.interfaceName}/`;

    if (!url.pathname.startsWith(prefix)) return null;

    return url;
}

export type InterceptedNavigateHandler = (url: URL) => void;

/**
 * Create a capture-phase click handler that claims in-interface navigations.
 *
 * @param scope A getter returning the current {@linkcode InterceptScope}. It is
 * invoked per event, so it must read `currentPathname` and `currentSearch` from
 * the live location at event time — otherwise fragment-only clicks cannot be
 * distinguished from real path navigations.
 * @param onIntercept Called with the resolved URL when a click is claimed.
 */
export function createClickInterceptor(
    scope: () => InterceptScope,
    onIntercept: InterceptedNavigateHandler,
): (event: MouseEvent) => void {
    return (event: MouseEvent) => {
        const anchor = event
            .composedPath()
            .find(
                (node): node is HTMLAnchorElement =>
                    node instanceof HTMLElement && node.nodeName === "A",
            );

        if (!anchor) return;

        const url = decideInterception(
            {
                button: event.button,
                metaKey: event.metaKey,
                ctrlKey: event.ctrlKey,
                shiftKey: event.shiftKey,
                altKey: event.altKey,
                defaultPrevented: event.defaultPrevented,
                target: anchor.getAttribute("target"),
                hasDownload: anchor.hasAttribute("download"),
                href: anchor.href || null,
            },
            scope(),
        );

        if (!url) return;

        event.preventDefault();
        onIntercept(url);
    };
}

//#endregion
