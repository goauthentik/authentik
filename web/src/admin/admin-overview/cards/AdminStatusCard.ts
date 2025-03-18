import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { PFSize } from "@goauthentik/common/enums.js";
import {
    APIError,
    parseAPIResponseError,
    pluckErrorDetail,
} from "@goauthentik/common/errors/network";
import { AggregateCard } from "@goauthentik/elements/cards/AggregateCard";

import { msg } from "@lit/localize";
import { PropertyValues, TemplateResult, html, nothing } from "lit";
import { state } from "lit/decorators.js";

import { ResponseError } from "@goauthentik/api";

export interface AdminStatus {
    icon: string;
    message?: TemplateResult;
}

/**
 * Abstract base class for admin status cards with robust state management
 *
 * @template T - Type of the primary data value used in the card
 */
export abstract class AdminStatusCard<T> extends AggregateCard {
    // Current data value state
    @state()
    value?: T;

    // Current status state derived from value
    @state()
    protected status?: AdminStatus;

    // Current error state if any request fails
    @state()
    protected error?: APIError;

    // Abstract methods to be implemented by subclasses
    abstract getPrimaryValue(): Promise<T>;
    abstract getStatus(value: T): Promise<AdminStatus>;

    constructor() {
        super();
        // Proper binding for event handler
        this.fetchData = this.fetchData.bind(this);
        // Register refresh event listener
        this.addEventListener(EVENT_REFRESH, this.fetchData);
    }

    // Lifecycle method: Called when component is added to DOM
    connectedCallback(): void {
        super.connectedCallback();
        // Initial data fetch
        this.fetchData();
    }

    /**
     * Fetch primary data and handle errors
     */
    private fetchData() {
        this.getPrimaryValue()
            .then((value: T) => {
                this.value = value; // Triggers shouldUpdate
                this.error = undefined;
            })
            .catch(async (error) => {
                this.status = undefined;
                this.error = await parseAPIResponseError(error);
            });
    }

    /**
     * Lit lifecycle method: Determine if component should update
     *
     * @param changed - Map of changed properties
     * @returns boolean indicating if update should proceed
     */
    shouldUpdate(changed: PropertyValues<this>) {
        if (changed.has("value") && this.value !== undefined) {
            // When value changes, fetch new status
            this.getStatus(this.value)
                .then((status) => {
                    this.status = status;
                    this.error = undefined;
                })
                .catch(async (error: ResponseError) => {
                    this.status = undefined;
                    this.error = await parseAPIResponseError(error);
                });

            // Prevent immediate re-render if only value changed
            if (changed.size === 1) return false;
        }
        return true;
    }

    /**
     * Render the primary value display
     *
     * @returns TemplateResult displaying the value
     */
    protected renderValue(): TemplateResult {
        return html`${this.value}`;
    }

    /**
     * Render status state
     *
     * @param status - AdminStatus object containing icon and message
     * @returns TemplateResult for status display
     */
    private renderStatus(status: AdminStatus): TemplateResult {
        return html`
            <p><i class="${status.icon}"></i>&nbsp;${this.renderValue()}</p>
            ${status.message ? html`<p class="subtext">${status.message}</p>` : nothing}
        `;
    }

    /**
     * Render error state
     *
     * @param error - Error message to display
     * @returns TemplateResult for error display
     */
    private renderError(error: string): TemplateResult {
        return html`
            <p><i class="fa fa-times"></i>&nbsp;${msg("Failed to fetch")}</p>
            <p class="subtext">${error}</p>
        `;
    }

    /**
     * Render loading state
     *
     * @returns TemplateResult for loading spinner
     */
    private renderLoading(): TemplateResult {
        return html`<ak-spinner size="${PFSize.Large}"></ak-spinner>`;
    }

    /**
     * Main render method that selects appropriate state display
     *
     * @returns TemplateResult for current component state
     */
    renderInner(): TemplateResult {
        return html`
            <p class="center-value">
                ${
                    this.status
                        ? this.renderStatus(this.status) // Status available
                        : this.error
                          ? this.renderError(pluckErrorDetail(this.error)) // Error state
                          : this.renderLoading() // Loading state
                }
            </p>
        `;
    }
}
