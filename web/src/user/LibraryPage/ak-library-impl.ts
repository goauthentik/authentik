import "#elements/EmptyState";
import "#user/LibraryApplication/index";
import "./ak-library-application-empty-list.js";
import "./ak-library-application-list.js";
import "./ak-library-application-search-empty.js";
import "./ak-library-application-search.js";

import {
    LibraryPageSearchEmpty,
    LibraryPageSearchReset,
    LibraryPageSearchSelected,
    LibraryPageSearchUpdated,
} from "./events.js";
import styles from "./LibraryPageImpl.styles.js";
import { appHasLaunchUrl } from "./LibraryPageImpl.utils.js";
import type { PageUIConfig } from "./types.js";

import { groupBy } from "#common/utils";

import { AKElement } from "#elements/Base";

import type { Application } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

/**
 * List of Applications available
 *
 * Properties:
 * apps: a list of the applications available to the user.
 *
 * Aggregates two functions:
 *   - Display the list of applications available to the user
 *   - Filter that list using the search bar
 *
 */

@customElement("ak-library-impl")
export class LibraryPage extends AKElement {
    public static styles = styles;

    /**
     * Controls showing the "Switch to Admin" button.
     *
     * @attr
     */
    @property({ attribute: "isadmin", type: Boolean })
    public isAdmin = false;

    /**
     * The *complete* list of applications for this user. Not paginated.
     *
     * @attr
     */
    @property({ attribute: false, type: Array })
    public apps!: Application[];

    /**
     * The aggregate uiConfig, derived from user, brand, and instance data.
     *
     * @attr
     */
    @property({ attribute: false })
    public uiConfig!: PageUIConfig;

    @state()
    protected selectedApp?: Application;

    @state()
    protected filteredApps: Application[] = [];

    pageTitle(): string {
        return msg("My Applications");
    }

    public connectedCallback() {
        super.connectedCallback();
        this.filteredApps = this.apps;
        if (this.filteredApps === undefined) {
            throw new Error(
                "Application.results should never be undefined when passed to the Library Page.",
            );
        }
        this.addEventListener(LibraryPageSearchUpdated.eventName, this.#searchUpdated);
        this.addEventListener(LibraryPageSearchReset.eventName, this.#searchReset);
        this.addEventListener(LibraryPageSearchEmpty.eventName, this.#searchEmpty);
        this.addEventListener(LibraryPageSearchSelected.eventName, this.#launchRequest);
    }

    public disconnectedCallback() {
        this.removeEventListener(LibraryPageSearchUpdated.eventName, this.#searchUpdated);
        this.removeEventListener(LibraryPageSearchReset.eventName, this.#searchReset);
        this.removeEventListener(LibraryPageSearchEmpty.eventName, this.#searchEmpty);
        this.removeEventListener(LibraryPageSearchSelected.eventName, this.#launchRequest);
        super.disconnectedCallback();
    }

    #searchUpdated = (event: LibraryPageSearchUpdated) => {
        event.stopPropagation();
        const apps = event.apps;
        if (apps.length <= 0) {
            throw new Error(
                "LibaryPageSearchUpdated had empty results body. This must not happen.",
            );
        }
        this.filteredApps = apps;
        this.selectedApp = apps[0];
    };

    #launchRequest = (event: LibraryPageSearchSelected) => {
        event.stopPropagation();
        if (!this.selectedApp?.launchUrl) {
            return;
        }
        if (!this.selectedApp.openInNewTab) {
            window.location.assign(this.selectedApp?.launchUrl);
        } else {
            window.open(this.selectedApp.launchUrl);
        }
    };

    #searchReset = (event: LibraryPageSearchReset) => {
        event.stopPropagation();
        this.filteredApps = this.apps;
        this.selectedApp = undefined;
    };

    #searchEmpty = (event: LibraryPageSearchEmpty) => {
        event.stopPropagation();
        this.filteredApps = [];
        this.selectedApp = undefined;
    };

    protected renderApps() {
        const selected = this.selectedApp?.slug;
        const layout = this.uiConfig.layout as string;
        const background = this.uiConfig.background;
        const groupedApps = groupBy(
            this.filteredApps.filter(appHasLaunchUrl),
            (app) => app.group || "",
        );

        return html`<ak-library-application-list
            layout="${layout}"
            background="${ifDefined(background)}"
            selected="${ifDefined(selected)}"
            .apps=${groupedApps}
        ></ak-library-application-list>`;
    }

    protected renderSearch() {
        return html`<ak-library-application-search
            .apps=${this.apps}
        ></ak-library-application-search>`;
    }

    protected renderNoAppsFound() {
        return html`<ak-library-application-search-empty></ak-library-application-search-empty>`;
    }

    protected renderSearchEmpty() {
        return nothing;
    }

    protected renderState() {
        if (!this.apps.some(appHasLaunchUrl)) {
            return html`<ak-library-application-empty-list
                ?isadmin=${this.isAdmin}
            ></ak-library-application-empty-list>`;
        }
        return this.filteredApps.some(appHasLaunchUrl) // prettier-ignore
            ? this.renderApps()
            : this.renderNoAppsFound();
    }

    public render() {
        return html`<main role="main" class="pf-c-page__main" tabindex="-1" id="main-content">
            <div class="pf-c-content header">
                <h1 role="heading" aria-level="1" id="library-page-title">
                    ${msg("My applications")}
                </h1>
                ${this.uiConfig.searchEnabled ? this.renderSearch() : nothing}
            </div>
            <section class="pf-c-page__main-section">${this.renderState()}</section>
        </main>`;
    }
}
