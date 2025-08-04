import type { Application } from "@goauthentik/api";

/**
 * @class LibraryPageSearchUpdated
 *
 * Indicates that the user has made a query that resulted in some
 * applications being filtered-for.
 *
 */
export class LibraryPageSearchUpdated extends Event {
    public static readonly eventName = "authentik.library.search-updated";
    /**
     * @attr apps: The list of those entries found by the current search.
     */
    public constructor(public apps: Application[]) {
        super(LibraryPageSearchUpdated.eventName, { composed: true, bubbles: true });
    }
}

/**
 * @class LibraryPageSearchReset
 *
 * Indicates that the user has emptied the search field. Intended to
 * signal that all available apps are to be displayed.
 *
 */
export class LibraryPageSearchReset extends Event {
    public static readonly eventName = "authentik.library.search-reset";
    public constructor() {
        super(LibraryPageSearchReset.eventName, { composed: true, bubbles: true });
    }
}

/**
 * @class LibraryPageSearchEmpty
 *
 * Indicates that the user has made a query that resulted in an empty
 * list being returned. Intended to signal that an alternative "No
 * matching applications found" message be displayed.
 *
 */
export class LibraryPageSearchEmpty extends Event {
    public static readonly eventName = "authentik.library.search-empty";

    public constructor() {
        super(LibraryPageSearchEmpty.eventName, { composed: true, bubbles: true });
    }
}

/**
 * @class LibraryPageSearchEmpty
 *
 * Indicates that the user has pressed "Enter" while focused on the
 * search box. Intended to signal that the currently highlighted search
 * entry (if any) should be activated.
 *
 */
export class LibraryPageSearchSelected extends Event {
    public static readonly eventName = "authentik.library.search-item-selected";
    public constructor() {
        super(LibraryPageSearchSelected.eventName, { composed: true, bubbles: true });
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        [LibraryPageSearchUpdated.eventName]: LibraryPageSearchUpdated;
        [LibraryPageSearchReset.eventName]: LibraryPageSearchReset;
        [LibraryPageSearchEmpty.eventName]: LibraryPageSearchEmpty;
        [LibraryPageSearchSelected.eventName]: LibraryPageSearchSelected;
    }
}
