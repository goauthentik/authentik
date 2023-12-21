import { groupBy } from "@goauthentik/common/utils";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/EmptyState";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import "@goauthentik/user/LibraryApplication";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import styles from "./LibraryPageImpl.css";

import type { Application } from "@goauthentik/api";

import "./ApplicationEmptyState";
import "./ApplicationList";
import "./ApplicationSearch";
import { appHasLaunchUrl } from "./LibraryPageImpl.utils";
import { SEARCH_ITEM_SELECTED, SEARCH_UPDATED } from "./constants";
import { isCustomEvent, loading } from "./helpers";
import type { AppGroupList, PageUIConfig } from "./types";

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
    static styles = styles;

    @property({ attribute: "isadmin", type: Boolean })
    isAdmin = false;

    @property({ attribute: false })
    apps!: PaginatedResponse<Application>;

    @property({ attribute: false })
    uiConfig!: PageUIConfig;

    @state()
    selectedApp?: Application;

    @state()
    filteredApps: Application[] = [];

    constructor() {
        super();
        this.searchUpdated = this.searchUpdated.bind(this);
        this.launchRequest = this.launchRequest.bind(this);
    }

    pageTitle(): string {
        return msg("My Applications");
    }

    connectedCallback() {
        super.connectedCallback();
        this.filteredApps = this.apps?.results;
        if (this.filteredApps === undefined) {
            throw new Error(
                "Application.results should never be undefined when passed to the Library Page.",
            );
        }
        this.addEventListener(SEARCH_UPDATED, this.searchUpdated);
        this.addEventListener(SEARCH_ITEM_SELECTED, this.launchRequest);
    }

    disconnectedCallback() {
        this.removeEventListener(SEARCH_UPDATED, this.searchUpdated);
        this.removeEventListener(SEARCH_ITEM_SELECTED, this.launchRequest);
        super.disconnectedCallback();
    }

    searchUpdated(event: Event) {
        if (!isCustomEvent(event)) {
            throw new Error("ak-library-search-updated must send a custom event.");
        }
        event.stopPropagation();
        const apps = event.detail.apps;
        this.selectedApp = undefined;
        this.filteredApps = this.apps.results;
        if (apps.length > 0) {
            this.selectedApp = apps[0];
            this.filteredApps = event.detail.apps;
        }
    }

    launchRequest(event: Event) {
        if (!isCustomEvent(event)) {
            throw new Error("ak-library-item-selected must send a custom event");
        }
        event.stopPropagation();
        const location = this.selectedApp?.launchUrl;
        if (location) {
            window.location.assign(location);
        }
    }

    getApps(): AppGroupList {
        return groupBy(this.filteredApps.filter(appHasLaunchUrl), (app) => app.group || "");
    }

    renderEmptyState() {
        return html`<ak-library-application-empty-list
            ?isadmin=${this.isAdmin}
        ></ak-library-application-empty-list>`;
    }

    renderApps() {
        const selected = this.selectedApp?.slug;
        const apps = this.getApps();
        const layout = this.uiConfig.layout as string;
        const background = this.uiConfig.background;

        return html`<ak-library-application-list
            layout="${layout}"
            background="${ifDefined(background)}"
            selected="${ifDefined(selected)}"
            .apps=${apps}
        ></ak-library-application-list>`;
    }

    renderSearch() {
        return html`<ak-library-list-search .apps=${this.apps.results}></ak-library-list-search>`;
    }

    render() {
        return html`<main role="main" class="pf-c-page__main" tabindex="-1" id="main-content">
            <div class="pf-c-content header">
                <h1 role="heading" aria-level="1" id="library-page-title">
                    ${msg("My applications")}
                </h1>
                ${this.uiConfig.searchEnabled ? this.renderSearch() : html``}
            </div>
            <section class="pf-c-page__main-section">
                ${loading(
                    this.apps,
                    html`${this.filteredApps.find(appHasLaunchUrl)
                        ? this.renderApps()
                        : this.renderEmptyState()}`,
                )}
            </section>
        </main>`;
    }
}
