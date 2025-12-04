import "#elements/EmptyState";
import "#user/LibraryApplication/index";
import "./ak-library-application-empty-list.js";

import Styles from "./ak-library-impl.css";
import AKLibraryApplicationListStyles from "./ApplicationList.css";
import { AKLibraryApplicationList } from "./ApplicationList.js";
import { appHasLaunchUrl } from "./LibraryPageImpl.utils.js";

import { groupBy } from "#common/utils";

import { AKSkipToContent } from "#elements/a11y/ak-skip-to-content";
import { AKElement } from "#elements/Base";
import { intersectionObserver } from "#elements/decorators/intersection-observer";
import { canAccessAdmin, WithSession } from "#elements/mixins/session";
import { getURLParam, updateURLParams } from "#elements/router/RouteMatch";
import { ifPresent } from "#elements/utils/attributes";
import { FocusTarget } from "#elements/utils/focus";
import { isInteractiveElement } from "#elements/utils/interactivity";
import { isFirefox } from "#elements/utils/useragent";

import type { Application } from "@goauthentik/api";

import Fuse from "fuse.js";

import { msg, str } from "@lit/localize";
import { html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { createRef } from "lit/directives/ref.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDivider from "@patternfly/patternfly/components/Divider/divider.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import PFSpacing from "@patternfly/patternfly/utilities/Spacing/spacing.css";

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
export class LibraryPage extends WithSession(AKElement) {
    /**
     * Maximum number of items to show in the datalist for search suggestions.
     */
    static readonly MAX_DATA_LIST_ITEMS = 5;
    /**
     * Whether to enable the datalist for search suggestions.
     *
     * @remarks
     * Disabled on Firefox due to performance issues between renders.
     */
    static DataListEnabled = !isFirefox();

    static styles = [
        // ---

        PFDisplay,
        PFEmptyState,
        PFPage,
        PFContent,
        PFFormControl,
        PFButton,
        PFCard,
        PFDivider,
        PFDropdown,
        PFGrid,
        PFSpacing,
        AKLibraryApplicationListStyles,
        Styles,
    ];

    //#region Properties

    /**
     * Controls showing the "Switch to Admin" button.
     */
    public get admin() {
        return canAccessAdmin(this.currentUser);
    }

    #applications: Application[] = [];

    /**
     * The *complete* list of applications for this user. Not paginated.
     *
     * @attr
     */
    @property({ attribute: false, type: Array })
    public get apps(): Application[] {
        return this.#applications;
    }

    public set apps(value: Application[]) {
        this.#applications = value;

        this.fuse.setCollection(this.searchEnabled ? this.#applications : []);
    }

    public get searchEnabled(): boolean {
        return this.uiConfig.enabledFeatures.search ?? true;
    }

    //#endregion

    //#region State

    protected autofocusTarget = new FocusTarget<HTMLInputElement>();
    public override focus = () => this.autofocusTarget.focus({ preventScroll: true });

    protected get selectedApp(): Application | null {
        if (!this.query) return null;

        return this.visibleApplications[0] || null;
    }

    @intersectionObserver()
    public visible = false;

    @state()
    protected visibleApplications: Application[] = [];

    /**
     * The active element to select when the user presses Enter outside of a form.
     */
    protected targetRef = createRef<HTMLElement>();

    #query: string | null = null;

    protected get query(): string | null {
        return this.#query;
    }

    protected set query(nextQuery: string | null) {
        this.#query = nextQuery;

        if (nextQuery && this.searchEnabled) {
            this.visibleApplications = this.fuse
                .search(nextQuery)
                .map((result) => result.item)
                .filter(appHasLaunchUrl);
        } else {
            this.visibleApplications = this.apps.filter(appHasLaunchUrl);
        }

        updateURLParams({
            q: this.#query,
        });
    }

    protected fuse = new Fuse<Application>([], {
        keys: [
            { name: "name", weight: 3 },
            "slug",
            "group",
            { name: "metaDescription", weight: 0.5 },
            { name: "metaPublisher", weight: 0.5 },
        ],
        findAllMatches: true,
        includeScore: true,
        shouldSort: true,
        ignoreFieldNorm: true,
        useExtendedSearch: true,
        threshold: 0.3,
    });

    public pageTitle = msg("My Applications");

    //#region Lifecycle

    public override connectedCallback() {
        super.connectedCallback();

        this.query = getURLParam<string | null>("q", "");

        this.addEventListener(
            "focus",
            this.autofocusTarget.toEventListener({
                preventScroll: true,
            }),
        );

        document.addEventListener("visibilitychange", this.#visibilityListener);

        window.addEventListener("keydown", this.#rootKeyDownListener);
    }

    public override disconnectedCallback() {
        super.disconnectedCallback();

        document.removeEventListener("visibilitychange", this.#visibilityListener);
        window.removeEventListener("keydown", this.#rootKeyDownListener);
    }

    public override firstUpdated(changedProperties: PropertyValues<this>): void {
        super.firstUpdated(changedProperties);

        requestAnimationFrame(() => {
            this.focus();
            const { target } = this.autofocusTarget;

            if (!target) return;

            // Place cursor at end of input.
            target.selectionEnd = target.value.length;
            target.selectionStart = target.value.length;
        });
    }

    //#endregion

    //#region Event Listeners

    #inputListener = (event: KeyboardEvent) => {
        const inputElement = event.target as HTMLInputElement;

        this.query = inputElement.value;
    };

    #changeListener = () => {
        if (this.targetRef.value && this.visibleApplications.length === 1) {
            this.targetRef.value.focus();
            this.targetRef.value.click();
            return;
        }
    };

    #submitListener = (event: SubmitEvent) => {
        event.preventDefault();

        if (this.targetRef.value) {
            this.targetRef.value.focus();
            this.targetRef.value.click();

            return;
        }
    };

    #rootKeyDownListener = (event: KeyboardEvent) => {
        if (event.defaultPrevented || event.key !== "Enter") {
            return;
        }

        if (this.autofocusTarget.target?.matches(":focus")) {
            // Let the input handle the event.
            return;
        }

        if (this.renderRoot instanceof ShadowRoot) {
            const focusedElement = this.renderRoot.activeElement;
            if (isInteractiveElement(focusedElement)) {
                focusedElement.click();
            }
        }
    };

    #visibilityListener = () => {
        if (document.visibilityState !== "visible") return;
        if (!this.visible) return;

        this.focus();
    };

    //#endregion

    //#region Rendering

    renderApps() {
        const { currentUser, selectedApp } = this;
        const { layout, theme, enabledFeatures } = this.uiConfig;

        const editable = currentUser?.isSuperuser && enabledFeatures.applicationEdit;

        const groupedApps = groupBy(this.visibleApplications, (app) => app.group || "").sort(
            ([groupLabelA, groupAppsA], [groupLabelB, groupAppsB]) => {
                if (selectedApp) {
                    if (groupAppsA.includes(selectedApp)) return -1;
                    if (groupAppsB.includes(selectedApp)) return 1;
                }

                return groupLabelA.localeCompare(groupLabelB);
            },
        );

        return AKLibraryApplicationList({
            editable,
            layout: layout.type,
            background: theme.cardBackground,
            selectedApp,
            groupedApps,
            targetRef: this.targetRef,
        });
    }

    protected renderSearch() {
        return html`<search title=${msg("Applications")}>
            <form @submit=${this.#submitListener} id="application-search-form">
                <input
                    ${this.autofocusTarget.toRef()}
                    part="search-input"
                    name="application-search"
                    id="application-search-input"
                    @input=${this.#inputListener}
                    @change=${this.#changeListener}
                    type="search"
                    autocomplete="off"
                    spellcheck="false"
                    class="pf-c-form-control"
                    autofocus
                    placeholder=${msg("Search for an application by name...")}
                    value=${ifPresent(this.query)}
                    list=${ifPresent(LibraryPage.DataListEnabled, "application-search-options")}
                />
                ${this.renderDataList()}
            </form>
        </search>`;
    }

    protected renderDataList() {
        if (!LibraryPage.DataListEnabled) {
            return nothing;
        }

        return html`<datalist id="application-search-options">
            ${this.visibleApplications.slice(0, LibraryPage.MAX_DATA_LIST_ITEMS).map((app) => {
                return html`<option value=${app.name}></option>`;
            })}
        </datalist>`;
    }

    protected renderNoAppsFound() {
        return html`<div class="pf-c-empty-state pf-m-full-height" tabindex="-1">
            <div class="pf-c-empty-state__content">
                <i class="fas fa-cubes pf-c-empty-state__icon" aria-hidden="true"></i>
                <h3 class="pf-c-title pf-m-lg" id="no-results-title">
                    ${msg("Search returned no results.")}
                </h3>
            </div>
        </div>`;
    }

    protected renderState() {
        if (!this.apps.some(appHasLaunchUrl)) {
            return html`<ak-library-application-empty-list
                ?admin=${this.admin}
            ></ak-library-application-empty-list>`;
        }

        if (this.visibleApplications.length) {
            return this.renderApps();
        }

        return this.renderNoAppsFound();
    }

    public override render() {
        const count = this.visibleApplications.length;
        const { query } = this;

        let message: string;

        if (query) {
            // We must present the count within the label to ensure that the screen reader
            // considers the update significant enough to read on each change,
            // rather than the on just the first render.
            message =
                count === 1
                    ? msg(str`${count} application found for "${query}"`)
                    : msg(str`${count} applications found for "${query}"`);
        } else {
            message =
                count === 1
                    ? msg(str`${count} application available`)
                    : msg(str`${count} applications available`);
        }

        return html`<div class="pf-c-page__main">
            <div class="pf-c-page__header pf-c-content">
                <h1 class="pf-c-page__title">${msg("My applications")}</h1>
                ${this.searchEnabled ? this.renderSearch() : nothing}
            </div>
            <main
                ${AKSkipToContent.ref}
                id="main-content"
                class="pf-c-page__main-section"
                aria-label=${msg("Application list")}
            >
                <output
                    class="sr-only"
                    for="application-search-input"
                    form="application-search-form"
                    aria-live="polite"
                >
                    <p>${message}</p>
                </output>
                ${this.renderState()}
            </main>
        </div>`;
    }

    //#endregion
}
