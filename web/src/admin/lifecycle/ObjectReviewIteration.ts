import "#admin/lifecycle/LifecyclePreviewBanner";
import "#components/ak-textarea-input";
import "#elements/forms/ModalForm";
import "#elements/timestamp/ak-timestamp";
import "#admin/lifecycle/ObjectReviewForm";

import { createPaginatedResponse } from "#common/api/responses";
import { EVENT_REFRESH } from "#common/constants";

import { PaginatedResponse, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { LifecycleIterationStatus } from "#admin/lifecycle/utils";

import { LifecycleIteration, LifecycleIterationStateEnum, Review } from "@goauthentik/api";

import { match, P } from "ts-pattern";

import { msg, str } from "@lit/localize";
import { html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

@customElement("ak-object-review-iteration")
export class ObjectReviewIteration extends Table<Review> {
    static styles = [
        // ---
        ...super.styles,
        PFGrid,
        PFBanner,
        PFCard,
        PFFlex,
        PFDescriptionList,
    ];

    //#region Public Properties

    @property({ attribute: false })
    public iteration: LifecycleIteration | null = null;

    public override paginated = false;

    //#endregion

    //#region Protected Properties

    protected override emptyStateMessage = msg("No reviews yet.");

    protected columns: TableColumn[] = [
        [msg("Reviewed on"), "timestamp"],
        [msg("Reviewer"), "reviewer"],
        [msg("Note"), "note"],
    ];

    //#region Lifecycle

    protected updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        if (changedProperties.has("iteration")) {
            this.fetch();
        }
    }

    protected apiEndpoint(): Promise<PaginatedResponse<Review>> {
        if (!this.iteration) {
            return Promise.resolve(createPaginatedResponse<Review>());
        }

        return Promise.resolve(createPaginatedResponse(this.iteration.reviews));
    }

    #triggerRefresh = () => {
        this.dispatchEvent(
            new CustomEvent(EVENT_REFRESH, {
                bubbles: true,
                composed: true,
            }),
        );
    };

    //#endregion

    //#region Rendering

    //#region Summary Card

    protected renderReviewers(): SlottedTemplateResult {
        if (!this.iteration) {
            return html`<span>${msg("No review iteration found for this object.")}</span>`;
        }

        const { reviewers, reviewerGroups, minReviewers } = this.iteration.rule;

        const result: TemplateResult[] = [];

        if (reviewers.length) {
            result.push(html` <div>${reviewers.map((u) => u.name).join(", ")}</div>`);
        }

        const groupList = reviewerGroups.map((g) => g.name).join(", ");

        const label =
            minReviewers === 1
                ? reviewerGroups.length === 1
                    ? msg(str`At least ${minReviewers} user from this group: ${groupList}.`)
                    : msg(str`At least ${minReviewers} user from these groups: ${groupList}.`)
                : reviewerGroups.length === 1
                  ? msg(str`At least ${minReviewers} users from this group: ${groupList}.`)
                  : msg(str`At least ${minReviewers} users from these groups: ${groupList}.`);

        result.push(html` <div>${label}</div>`);

        return result;
    }

    protected renderOpenedOn(): SlottedTemplateResult {
        return html` <div class="pf-c-description-list__group">
            <dt class="pf-c-description-list__term">
                <span class="pf-c-description-list__text">${msg("Review opened on")}</span>
            </dt>
            <dd class="pf-c-description-list__description">
                <div class="pf-c-description-list__text">
                    <ak-timestamp
                        .timestamp=${this.iteration?.openedOn}
                        .elapsed=${false}
                        dateonly
                        datetime
                    ></ak-timestamp>
                </div>
            </dd>
        </div>`;
    }

    protected renderGracePeriodTill(): SlottedTemplateResult {
        return html` <div class="pf-c-description-list__group">
            <dt class="pf-c-description-list__term">
                <span class="pf-c-description-list__text">${msg("Grace period till")}</span>
            </dt>
            <dd class="pf-c-description-list__description">
                <div class="pf-c-description-list__text">
                    <ak-timestamp
                        .timestamp=${this.iteration?.gracePeriodEnd}
                        .elapsed=${false}
                        dateonly
                        datetime
                    ></ak-timestamp>
                </div>
            </dd>
        </div>`;
    }

    protected renderNextReviewDate(): SlottedTemplateResult {
        return html` <div class="pf-c-description-list__group">
            <dt class="pf-c-description-list__term">
                <span class="pf-c-description-list__text">${msg("Next review date")}</span>
            </dt>
            <dd class="pf-c-description-list__description">
                <div class="pf-c-description-list__text">
                    <ak-timestamp
                        .timestamp=${this.iteration?.nextReviewDate}
                        .elapsed=${false}
                        dateonly
                        datetime
                    ></ak-timestamp>
                </div>
            </dd>
        </div>`;
    }

    protected renderReviewDates() {
        return match(this.iteration?.state)
            .with(P.nullish, LifecycleIterationStateEnum.UnknownDefaultOpenApi, () => nothing)
            .with(
                LifecycleIterationStateEnum.Pending,
                () => html`${this.renderOpenedOn()}${this.renderGracePeriodTill()}`,
            )
            .with(LifecycleIterationStateEnum.Reviewed, () => this.renderNextReviewDate())
            .with(LifecycleIterationStateEnum.Overdue, () => this.renderOpenedOn())
            .with(LifecycleIterationStateEnum.Canceled, () => this.renderOpenedOn())
            .exhaustive();
    }

    protected renderReviewSummary() {
        return html` <div class="pf-c-card pf-l-grid__item pf-m-3-col">
            <div class="pf-c-card__title">${msg("Latest review for this object")}</div>
            <div class="pf-c-card__body">
                <dl class="pf-c-description-list">
                    <div class="pf-c-description-list__group">
                        <dt class="pf-c-description-list__term">
                            <span class="pf-c-description-list__text">${msg("Review state")}</span>
                        </dt>
                        <dd class="pf-c-description-list__description">
                            <div class="pf-c-description-list__text">
                                ${LifecycleIterationStatus({
                                    status: this.iteration?.state,
                                })}
                            </div>
                        </dd>
                    </div>

                    <div class="pf-c-description-list__group">
                        <dt class="pf-c-description-list__term">
                            <span class="pf-c-description-list__text"
                                >${msg("Required reviewers")}</span
                            >
                        </dt>
                        <dd class="pf-c-description-list__description">
                            <div class="pf-c-description-list__text">${this.renderReviewers()}</div>
                        </dd>
                    </div>
                    ${this.renderReviewDates()}
                </dl>
            </div>
        </div>`;
    }

    //#endregion

    //#region Table

    protected renderToolbar(): SlottedTemplateResult {
        return html`${this.renderObjectCreate()}
            <ak-spinner-button .callAction=${this.#triggerRefresh} class="pf-m-secondary">
                ${msg("Refresh")}
            </ak-spinner-button>`;
    }

    protected row(item: Review): SlottedTemplateResult[] {
        return [
            Timestamp(item.timestamp),
            html`<span>${item.reviewer.name}</span>`,
            html`<span>${item.note}</span>`,
        ];
    }

    protected override renderEmpty(): TemplateResult {
        return super.renderEmpty(
            html` <ak-empty-state icon="pf-icon-task"
                ><span>${this.emptyStateMessage}</span></ak-empty-state
            >`,
        );
    }

    protected renderObjectCreate(): SlottedTemplateResult {
        if (!this.iteration?.userCanReview) {
            return nothing;
        }

        return html` <ak-forms-modal>
            <span slot="submit">${msg("Confirm Review")}</span>
            <span slot="header">${msg("Confirm this object has been reviewed")}</span>
            <ak-object-review-form slot="form" .iteration=${this.iteration}>
            </ak-object-review-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${msg("Confirm Review")}
            </button>
        </ak-forms-modal>`;
    }

    protected override render(): SlottedTemplateResult {
        return html` <div class="pf-l-grid pf-m-gutter">
            ${this.renderReviewSummary()}
            <div class="pf-c-card pf-l-grid__item pf-m-9-col">
                <div class="pf-c-card__title">${msg("Reviews")}</div>
                <div class="pf-c-card__body">${super.render()}</div>
            </div>
        </div>`;
    }

    //#endregion

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-object-review-iteration": ObjectReviewIteration;
    }
}
