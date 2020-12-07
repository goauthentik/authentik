import { gettext } from "django";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { Application } from "../../api/application";
import { DefaultClient, PBResponse } from "../../api/client";
import { PolicyBinding } from "../../api/policy_binding";
import { COMMON_STYLES } from "../../common/styles";
import { Table } from "../../elements/table/Table";

import "../../elements/Tabs";
import "../../elements/AdminLoginsChart";
import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";

@customElement("ak-bound-policies-list")
export class BoundPoliciesList extends Table<PolicyBinding> {
    @property()
    target?: string;

    apiEndpoint(page: number): Promise<PBResponse<PolicyBinding>> {
        return DefaultClient.fetch<PBResponse<PolicyBinding>>(["policies", "bindings"], {
            target: this.target || "",
            ordering: "order",
            page: page,
        });
    }

    columns(): string[] {
        return ["Policy", "Enabled", "Order", "Timeout", ""];
    }

    row(item: PolicyBinding): string[] {
        return [
            item.policy_obj.name,
            item.enabled ? "Yes" : "No",
            item.order.toString(),
            item.timeout.toString(),
            `
            <ak-modal-button href="administration/policies/bindings/${item.pk}/update/">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    Edit
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="administration/policies/bindings/${item.pk}/delete/">
                <ak-spinner-button slot="trigger" class="pf-m-danger">
                    Delete
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            `,
        ];
    }

    renderToolbar(): TemplateResult {
        const createUrl = `/administration/policies/bindings/create/?target=${this.target}`;
        return html`
        <ak-modal-button href=${createUrl}>
            <ak-spinner-button slot="trigger" class="pf-m-primary">
                ${gettext("Create")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        ${super.renderToolbar()}
        `;
    }
}

@customElement("ak-application-view")
export class ApplicationViewPage extends LitElement {
    @property()
    set args(value: { [key: string]: string }) {
        this.applicationSlug = value.slug;
    }

    @property()
    set applicationSlug(value: string) {
        Application.get(value).then((app) => (this.application = app));
    }

    @property({attribute: false})
    application?: Application;

    static get styles(): CSSResult[] {
        return COMMON_STYLES.concat(
            css`
                img.pf-icon {
                    max-height: 24px;
                }
            `
        );
    }

    render(): TemplateResult {
        if (!this.application) {
            return html``;
        }
        return html`<section class="pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1>
                        <img class="pf-icon" src="${this.application?.meta_icon || ""}" />
                        ${this.application?.name}
                    </h1>
                    <p>${this.application?.meta_publisher}</p>
                </div>
            </section>
            <ak-tabs>
                <section slot="page-1" data-tab-title="Users" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-l-gallery pf-m-gutter">
                        <div class="pf-c-card pf-c-card-aggregate pf-l-gallery__item pf-m-4-col" style="grid-column-end: span 3;grid-row-end: span 2;">
                            <div class="pf-c-card__header">
                                <div class="pf-c-card__header-main">
                                    <i class="pf-icon pf-icon-server"></i> ${gettext("Logins over the last 24 hours")}
                                </div>
                            </div>
                            <div class="pf-c-card__body">
                                ${this.application ? html`
                                    <ak-admin-logins-chart
                                        url="${DefaultClient.makeUrl(["core", "applications", this.application?.slug, "metrics"])}">
                                    </ak-admin-logins-chart>`: ""}
                            </div>
                        </div>
                    </div>
                </section>
                <div slot="page-2" data-tab-title="Policy Bindings" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__header">
                            <div class="pf-c-card__header-main">
                                ${gettext("These policies control which users can access this application.")}
                            </div>
                        </div>
                        <ak-bound-policies-list .target=${this.application.pk}>
                        </ak-bound-policies-list>
                    </div>
                </div>
            </ak-tabs>`;
    }
}
