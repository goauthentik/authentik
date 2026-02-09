import "#admin/lifecycle/ReviewStastus";
import "#admin/lifecycle/LifecyclePreviewBanner";
import "#components/ak-textarea-input";
import "#elements/forms/ModalForm";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";
import { ModelForm } from "#elements/forms/ModelForm";
import { PaginatedResponse, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import {
    ContentTypeEnum,
    LifecycleApi,
    LifecycleIteration,
    LifecycleIterationStateEnum,
    Review,
} from "@goauthentik/api";

import { match } from "ts-pattern";

import { msg, str } from "@lit/localize";
import { html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-object-review-form")
export class ObjectReviewForm extends ModelForm<Review, string> {
    @property({ attribute: false })
    iteration!: LifecycleIteration;

    protected loadInstance(_pk: string): Promise<Review> {
        throw new Error("Reviews should not be edited.");
    }

    send(data: Review): Promise<unknown> {
        return new LifecycleApi(DEFAULT_CONFIG).lifecycleReviewsCreate({
            reviewRequest: data,
        });
    }

    protected override serialize(): Review | undefined {
        const review = super.serialize();
        if (!review) return undefined;
        review.iteration = this.iteration.id;
        return review;
    }

    renderForm(): TemplateResult {
        return html` <ak-textarea-input label=${msg("Note")} name="note"></ak-textarea-input> `;
    }
}

@customElement("ak-object-reviews")
export class ObejctReviews extends Table<Review> {
    @property({ attribute: false })
    public iteration?: LifecycleIteration;

    public override paginated = false;

    protected emptyStateMessage = msg("No reviews yet.");

    protected apiEndpoint(): Promise<PaginatedResponse<Review>> {
        const reviews = this?.iteration?.reviews || [];
        return Promise.resolve({
            results: reviews,
            pagination: {
                next: 0,
                previous: 0,
                count: reviews.length,
                current: 1,
                totalPages: 1,
                startIndex: 0,
                endIndex: reviews.length - 1,
            },
        });
    }

    protected override updated(changedProperties: PropertyValues<this>) {
        super.updated(changedProperties);
        if (changedProperties.has("iteration")) this.fetch();
    }

    protected columns: TableColumn[] = [
        [msg("Reviewed on"), "timestamp"],
        [msg("Reviewer"), "reviewer"],
        [msg("Note"), "note"],
    ];

    protected row(item: Review): SlottedTemplateResult[] {
        return [
            Timestamp(item.timestamp),
            html`<span>${item.reviewer.name}</span>`,
            html`<span>${item.note}</span>`,
        ];
    }

    protected renderToolbar(): TemplateResult {
        return html`${this.renderObjectCreate()}`;
    }

    protected renderObjectCreate(): SlottedTemplateResult {
        if (this.iteration?.userCanReview)
            return html`
                <ak-forms-modal>
                    <span slot="submit">${msg("Review")}</span>
                    <span slot="header"> ${msg("Confirm this object has been reviewed")} </span>
                    <ak-object-review-form slot="form" .iteration=${this.iteration}>
                    </ak-object-review-form>
                    <button slot="trigger" class="pf-c-button pf-m-primary">
                        ${msg("Review")}
                    </button>
                </ak-forms-modal>
            `;
        return nothing;
    }
}

@customElement("ak-object-lifecycle-page")
export class ObjectLifecyclePage extends AKElement {
    static styles = [PFBase, PFGrid, PFPage, PFBanner, PFCard, PFFlex, PFDescriptionList];

    @property()
    public model?: ContentTypeEnum;

    @property()
    objectPk?: string | number;

    @state()
    protected iteration?: LifecycleIteration | null;

    protected loading = false;

    protected fetchIteration() {
        if (!this.model || !this.objectPk || this.loading) {
            return;
        }
        this.loading = true;
        new LifecycleApi(DEFAULT_CONFIG)
            .lifecycleIterationsLatestRetrieve({
                contentType: this.model,
                objectId: this.objectPk.toString(),
            })
            .then((iteration) => {
                this.iteration = iteration;
                this.loading = false;
            })
            .catch((error) => {
                if (error.response.status === 404) {
                    this.iteration = null;
                }
                this.loading = false;
            });
    }

    #refreshListener = () => {
        return this.fetchIteration();
    };

    public override connectedCallback(): void {
        super.connectedCallback();
        this.addEventListener(EVENT_REFRESH, this.#refreshListener);
    }

    public override disconnectedCallback(): void {
        super.disconnectedCallback();
        this.removeEventListener(EVENT_REFRESH, this.#refreshListener);
    }

    protected override willUpdate(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("objectPk") && this.objectPk && this.checkVisibility()) {
            this.fetchIteration();
        }
    }

    protected renderReviewers() {
        if (!this.iteration) return;
        const ret: TemplateResult[] = [];
        if (this.iteration.reviewers.length > 0) {
            ret.push(html`<div>${this.iteration.reviewers.map((u) => u.name).join(", ")}</div>`);
        }
        const groupList = this.iteration.reviewerGroups.map((g) => g.name).join(", ");
        ret.push(
            html`<div>
                ${msg(
                    str`At least ${this.iteration.minReviewers} user(s) from these groups: ${groupList}.`,
                )}
            </div>`,
        );
        return ret;
    }

    protected renderOpenedOn() {
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

    protected renderGracePeriodTill() {
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

    protected renderNextReviewDate() {
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
            .with(undefined, LifecycleIterationStateEnum.UnknownDefaultOpenApi, () => nothing)
            .with(
                LifecycleIterationStateEnum.Pending,
                () => html`${this.renderOpenedOn()}${this.renderGracePeriodTill()}`,
            )
            .with(LifecycleIterationStateEnum.Reviewed, () => this.renderNextReviewDate())
            .with(LifecycleIterationStateEnum.Overdue, () => this.renderOpenedOn())
            .with(LifecycleIterationStateEnum.Canceled, () => this.renderOpenedOn())
            .exhaustive();
    }

    render() {
        if (this.iteration === undefined)
            return html` <ak-empty-state ?loading=${!this.iteration}
                >${msg("Loading...")}
            </ak-empty-state>`;
        if (!this.iteration)
            return html` <ak-empty-state>
                <div>${msg("This object does not have a review yet.")}</div>
            </ak-empty-state>`;
        return html` <ak-lifecycle-preview-banner></ak-lifecycle-preview-banner>
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-object-lifecycle"
                id="page-object-lifecycle"
                aria-label="${msg("Latest review for this object")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-l-grid pf-m-gutter">
                    <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                        <div class="pf-c-card__title">${msg("Latest review for this object")}</div>
                        <div class="pf-c-card__body">
                            <dl class="pf-c-description-list">
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text"
                                            >${msg("Review state")}</span
                                        >
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            <ak-lifecycle-review-status
                                                status=${this.iteration.state}
                                            ></ak-lifecycle-review-status>
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
                                        <div class="pf-c-description-list__text">
                                            ${this.renderReviewers()}
                                        </div>
                                    </dd>
                                </div>
                                ${this.renderReviewDates()}
                            </dl>
                        </div>
                    </div>

                    <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                        <div class="pf-c-card__title">${msg("Reviews")}</div>
                        <div class="pf-c-card__body">
                            <ak-object-reviews .iteration=${this.iteration}></ak-object-reviews>
                        </div>
                    </div>
                </div>
            </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-object-lifecycle-page": ObjectLifecyclePage;
    }
}
