import "#admin/lifecycle/LifecyclePreviewBanner";
import "#admin/lifecycle/ObjectReviewIteration";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";
import { isResponseErrorLike } from "#common/errors/network";

import { AKElement } from "#elements/Base";
import { WithLicenseSummary } from "#elements/mixins/license";
import { WithSession } from "#elements/mixins/session";
import Styles from "#elements/table/Table.css";
import { SlottedTemplateResult } from "#elements/types";
import { ifPreviousValue } from "#elements/utils/properties";

import { ContentTypeEnum, LifecycleApi, LifecycleIteration } from "@goauthentik/api";

import { html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFSpacing from "@patternfly/patternfly/utilities/Spacing/spacing.css";

@customElement("ak-object-lifecycle-page")
export class ObjectLifecyclePage extends WithLicenseSummary(WithSession(AKElement)) {
    static styles = [
        // ---
        PFTitle,
        PFGrid,
        PFBanner,
        Styles,
        PFSpacing,
    ];

    //#region Public Properties

    @property({ type: String })
    public model: ContentTypeEnum | null = null;

    @property({ attribute: "object-pk", hasChanged: ifPreviousValue, useDefault: true })
    public objectPk: string | number | null = null;

    //#endregion

    //#region Protected Properties

    //#region Lifecycle

    @state()
    protected iterations: LifecycleIteration[] | null = null;

    #refreshListener = () => {
        return this.fetch();
    };

    public override connectedCallback(): void {
        super.connectedCallback();
        this.addEventListener(EVENT_REFRESH, this.#refreshListener);
    }

    public async fetch(): Promise<void> {
        if (!this.model || !this.objectPk) {
            return Promise.resolve();
        }
        return new LifecycleApi(DEFAULT_CONFIG)
            .lifecycleIterationsListLatest({
                contentType: this.model,
                objectId: String(this.objectPk),
            })
            .then((iterations) => {
                this.iterations = iterations;
            })
            .catch(async (error: unknown) => {
                if (isResponseErrorLike(error) && error.response.status === 404) {
                    this.iterations = null;
                }
                throw error;
            });
    }

    //#endregion

    //#region Rendering

    protected override render(): SlottedTemplateResult {
        return html`<div class="pf-l-grid pf-m-gutter">
            <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                <ak-lifecycle-preview-banner></ak-lifecycle-preview-banner>
            </div>
            ${this.iterations?.map(
                (i) =>
                    html` <h2 class="pf-c-title pf-m-xl">${i.rule.name}</h2>
                        <ak-object-review-iteration
                            .iteration=${i}
                            class="pf-u-pl-lg-on-lg"
                        ></ak-object-review-iteration>`,
            )}
        </div> `;
    }

    //#endregion

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-object-lifecycle-page": ObjectLifecyclePage;
    }
}
