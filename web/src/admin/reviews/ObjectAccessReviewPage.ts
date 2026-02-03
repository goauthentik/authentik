import {AKElement} from "#elements/Base";


import {html, nothing, PropertyValues, TemplateResult} from "lit";
import {customElement, property, state} from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import {
    Attestation,
    ContentTypeEnum,
    Review,
    ReviewsApi,
    ReviewStateEnum
} from "@goauthentik/api";
import {msg} from "@lit/localize";
import {DEFAULT_CONFIG} from "#common/api/config";
import {PaginatedResponse, Table, TableColumn, Timestamp} from "#elements/table/Table";
import {SlottedTemplateResult} from "#elements/types";
import {ModelForm} from "#elements/forms/ModelForm";
import {EVENT_REFRESH} from "#common/constants";
import PFDescriptionList
    from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import "#admin/reviews/AccessReviewStastus";
import "#components/ak-textarea-input";
import "#elements/forms/ModalForm";


@customElement("ak-object-attestation-form")
export class ObjectAttestationForm extends ModelForm<Attestation, string> {
    @property({attribute: false})
    review!: Review;

    protected loadInstance(_pk: string): Promise<Attestation> {
        throw new Error("Attestations should not be edited.");
    }

    send(data: Attestation): Promise<unknown> {
        return new ReviewsApi(DEFAULT_CONFIG).reviewsAttestationsCreate({attestationRequest: data}).then(attestation => {
            this.review.attestations.push(attestation);
            this.dispatchEvent(
                new CustomEvent(EVENT_REFRESH, {
                    bubbles: true,
                    composed: true,
                }),
            );

            return attestation;
        });
    }

    protected override serialize(): Attestation | undefined {
        const attestation = super.serialize();
        if (!attestation) return undefined;
        attestation.review = this.review.id;
        return attestation;
    }

    renderForm(): TemplateResult {
        return html`
            <ak-textarea-input
                label=${msg("Note")}
                name="note"
            ></ak-textarea-input>
        `;
    }

}

@customElement("ak-access-review-attestations")
export class AccessReviewAttestations extends Table<Attestation> {

    @property({attribute: false})
    public review?: Review;

    public override paginated = false;

    protected emptyStateMessage = msg("No attestations yet.");

    protected apiEndpoint(): Promise<PaginatedResponse<Attestation>> {
        const attestations = this?.review?.attestations || [];
        return Promise.resolve({
            results: attestations,
            pagination: {
                next: 0,
                previous: 0,
                count: attestations.length,
                current: 0,
                totalPages: 1,
                startIndex: 0,
                endIndex: attestations.length - 1
            },
        });
    }

    protected columns: TableColumn[] = [
        [msg("Reviewed on"), "timestamp"],
        [msg("Reviewer"), "reviewer"],
        [msg("Note"), "note"],
    ];


    protected row(item: Attestation): SlottedTemplateResult[] {
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
        if (this.review?.userCanAttest)
            return html`
                <ak-forms-modal>
                    <span slot="submit">${msg("Attest")}</span>
                    <span slot="header">
                    ${msg("Attest this object's access")}
                </span>
                    <ak-object-attestation-form
                        slot="form"
                        .review=${this.review}
                    >
                    </ak-object-attestation-form>
                    <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Attest")}
                    </button>
                </ak-forms-modal>
            `;
        return nothing;
    }


}


@customElement("ak-object-access-review-page")
export class ObjectPermissionPage extends AKElement {
    @property()
    public model?: ContentTypeEnum;

    @property()
    objectPk?: string | number;

    @state()
    protected review?: Review | null;


    protected fetchReview() {
        if (!this.model || !this.objectPk) {
            return
        }
        new ReviewsApi(DEFAULT_CONFIG).reviewsReviewsLatestRetrieve({
            contentType: this.model,
            objectId: this.objectPk.toString()
        }).then(review => {
            this.review = review;
        }).catch(error => {
            if (error.response.status === 404) {
                this.review = null;
            }
        })
    }

    #refreshListener = () => {
        return this.fetchReview();
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
        if (changedProperties.has("objectPk") && this.objectPk) {
            this.fetchReview();
        }
    }


    static styles = [PFBase, PFGrid, PFPage, PFCard, PFDescriptionList];


    protected renderReviewers() {
        if (!this.review)
            return;
        if (this.review.reviewers.length > 0) {
            return html`${this.review.reviewers.map(u => u.name).join(", ")}`;
        }
        const groupList = this.review.reviewerGroups.map(g => g.name).join(", ");
        return html`${msg(`At least ${this.review.minReviewers} user(s) from these groups: ${groupList}.`)}`;

    }

    render() {
        if (this.review === undefined)
            return html`
                <ak-empty-state ?loading=${!this.review}>${msg("Loading...")}</ak-empty-state>`
        if (!this.review)
            return html`
                <ak-empty-state>
                    <div>${msg("This object does not have an access review yet.")}</div>
                </ak-empty-state>`
        return html`
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-object-access-review"
                id="page-object-access-review"
                aria-label="${msg("Access review for this object")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-l-grid pf-m-gutter">
                    <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                        <div class="pf-c-card__title">${msg("Access review for this object")}</div>
                        <div class="pf-c-card__body">

                            <dl class="pf-c-description-list">
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span
                                            class="pf-c-description-list__text">${msg("Review state")}</span>
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            <ak-access-review-status
                                                status=${this.review.state}></ak-access-review-status>
                                        </div>
                                    </dd>
                                </div>

                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span
                                            class="pf-c-description-list__text">${msg("Required reviewers")}</span>
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            ${this.renderReviewers()}
                                        </div>
                                    </dd>
                                </div>
                                ${this.review.state !== ReviewStateEnum.Reviewed ?
                                    html`
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                        <span
                                            class="pf-c-description-list__text">${msg("Review opened on")}</span>
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">
                                                    <ak-timestamp
                                                        .timestamp=${this.review?.openedOn}
                                                        .elapsed=${false} dateonly
                                                        datetime></ak-timestamp>
                                                </div>
                                            </dd>
                                        </div>` :
                                    html`
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                        <span
                                            class="pf-c-description-list__text">${msg("Next review date")}</span>
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">
                                                    <ak-timestamp
                                                        .timestamp=${this.review?.nextReviewDate}
                                                        .elapsed=${false} dateonly
                                                        datetime></ak-timestamp>
                                                </div>
                                            </dd>
                                        </div>`}
                                ${this.review.state === ReviewStateEnum.Pending ?
                                    html`
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                        <span
                                            class="pf-c-description-list__text">${msg("Grace period till")}</span>
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">
                                                    <ak-timestamp
                                                        .timestamp=${this.review?.gracePeriodEnd}
                                                        .elapsed=${false} dateonly
                                                        datetime></ak-timestamp>
                                                </div>
                                            </dd>
                                        </div>` : nothing}
                            </dl>
                        </div>
                    </div>

                    <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                        <div class="pf-c-card__title">${msg("Attestations")}</div>
                        <div class="pf-c-card__body">
                            <ak-access-review-attestations .review=${this.review}>
                            </ak-access-review-attestations>

                        </div>
                    </div>
                </div>
            </div>`
    }

}

declare global {
    interface HTMLElementTagNameMap {
        "ak-object-access-review-page": ObjectPermissionPage;
    }
}
