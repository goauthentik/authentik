import type { Application } from "@goauthentik/api";

export const AK_LIBRARY_SEARCH_UPDATED = "authentik.library.search-updated";
export const AK_LIBRARY_SEARCH_RESET = "authentik.library.search-reset";
export const AK_LIBRARY_SEARCH_EMPTY = "authentik.library.search-empty";
export const AK_LIBRARY_SEARCH_ITEM_SELECTED = "authentik.library.search-item-selected";

/**
 * @class LibraryPageSearchUpdated
 *
 * Indicates that the user has made a query that resulted in some applications being filtered-for.
 *
 */
export class LibraryPageSearchUpdated extends Event {
    /**
     * The list of those entries found by the current search.
     *
     * @attr
     */
    public apps: Application[];

    constructor(apps: Application[]) {
        super(AK_LIBRARY_SEARCH_UPDATED, { composed: true, bubbles: true });
        this.apps = apps;
    }
}

/**
 * @class LibraryPageSearchReset
 *
 * Indicates that the user has emptied the search field. Intended to signal that all available apps
 * to be displayed.
 *
 */
export class LibraryPageSearchReset extends Event {
    constructor() {
        super(AK_LIBRARY_SEARCH_RESET, { composed: true, bubbles: true });
    }
}

/**
 * @class LibraryPageSearchEmpty
 *
 * Indicates that the user has made a query that resulted in an empty list being returned. Intended
 * to signal that an alternative "No matching applications found" message be displayed.
 *
 */
export class LibraryPageSearchEmpty extends Event {
    constructor() {
        super(AK_LIBRARY_SEARCH_EMPTY, { composed: true, bubbles: true });
    }
}

/**
 * @class LibraryPageSearchEmpty
 *
 * Indicates that the user has pressed "Enter" while focused on the search box. Intended to signal
 * that the currently highlighted search entry (if any) should be activated.
 *
 */
export class LibraryPageSearchSelected extends Event {
    constructor() {
        super(AK_LIBRARY_SEARCH_ITEM_SELECTED, { composed: true, bubbles: true });
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        [AK_LIBRARY_SEARCH_UPDATED]: LibraryPageSearchUpdated;
        [AK_LIBRARY_SEARCH_RESET]: LibraryPageSearchReset;
        [AK_LIBRARY_SEARCH_EMPTY]: LibraryPageSearchEmpty;
        [AK_LIBRARY_SEARCH_ITEM_SELECTED]: LibraryPageSearchSelected;
    }
}
