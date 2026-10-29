import { BookmarkChangeEvent } from "./bookmarkChangeEvent";
import { BookmarkContext } from "./BookmarkController";
import { Bookmark } from "./bookmarkState";

import { Bookmark as BookmarkComponent } from "#elements/Bookmark";

import { BreadcrumbContext, BreadcrumbEntries } from "#admin/sidebar/BreadcrumbController";

import { consume } from "@lit/context";
import { PropertyValues } from "lit";
import { customElement, query } from "lit/decorators.js";

@customElement("ak-ui-bookmark")
export class AkBookmark extends BookmarkComponent {
    protected sendBookmarkEvent = (ev: Event) => {
        const crumb = this.crumbs?.crumbs.at(-1);
        if (!(crumb && crumb.path)) {
            return;
        }
        ev.stopPropagation();

        this.dispatchEvent(
            new BookmarkChangeEvent({
                path: crumb.path,
                label: crumb.label,
                add: this.state === "unmarked", // "I want to add if it's currently unmarked"
            }),
        );
    };

    constructor() {
        super();
        this.addEventListener("click", this.sendBookmarkEvent);
    }

    /**
     * The collection of bookmarks, so we can tell if "ours" is here.
     */
    @consume({ context: BookmarkContext, subscribe: true })
    public bookmarks: Bookmark[] | null = null;

    /**
     * The current collection of Breadcrumbs
     */
    @consume({ context: BreadcrumbContext, subscribe: true })
    public crumbs: BreadcrumbEntries | null = null;

    /**
     * The object this page shows, without any tab suffix; null on list pages.
     */
    public bookmark: Bookmark | null = null;

    // [Lit Lifecycle](https://lit.dev/docs/components/lifecycle/#willupdate)
    public override willUpdate(changed: PropertyValues<this>) {
        super.willUpdate(changed);

        // The object crumb is available after the page header has filled in the object's name.
        const objectPath = this.crumbs?.objectPath ?? null;
        const crumb = this.crumbs?.crumbs.at(-1);

        this.bookmark =
            objectPath && crumb?.path === objectPath
                ? { path: objectPath, label: crumb.label }
                : null;

        this.state = !this.bookmark
            ? "hidden"
            : this.bookmarks?.some(({ path }) => path === objectPath)
              ? "marked"
              : "unmarked";
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-ui-bookmark": AkBookmark;
    }
}
