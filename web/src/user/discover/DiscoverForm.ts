import "../../elements/AppIcon";

import { aki } from "#common/api/client";
import { PFSize } from "#common/enums";

import { Form } from "#elements/forms/Form";
import { PaginatedResponse } from "#elements/table/shared";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import {
    Application,
    CoreApi,
    GrantRequestCreateRequest,
    PamApi,
    RequestableTarget,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css } from "lit";
import { html, nothing } from "lit-html";
import { customElement, state } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFCheck from "@patternfly/patternfly/components/Check/check.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

@customElement("ak-discover-form")
export class DiscoverForm extends Form<GrantRequestCreateRequest> {
    public static override createLabel = null;
    public static submitVerb: string = msg("Request");

    static styles = [
        ...super.styles,
        PFCard,
        PFGrid,
        PFCheck,
        css`
            .pf-l-grid {
                padding: 1rem 0;
            }
            .pf-c-card {
                display: flex;
                flex-direction: column;
            }
            .ak-requestable-entitlements {
                margin-top: 0.5rem;
                padding-top: 0.5rem;
                border-top: 1px solid var(--pf-global--BorderColor--100);
            }
        `,
    ];

    @state()
    apps?: PaginatedResponse<Application>;

    @state()
    entitlements?: RequestableTarget[];

    @state()
    selectedApps: Application[] = [];

    @state()
    selectedEntitlements: RequestableTarget[] = [];

    public override async connectedCallback(): Promise<void> {
        super.connectedCallback();

        const [apps, entitlements] = await Promise.all([
            aki(CoreApi).coreApplicationsRequestableList({}),
            aki(CoreApi).coreApplicationEntitlementsRequestableList({}),
        ]);
        this.apps = apps;
        this.entitlements = entitlements.results;
    }

    protected send(_data: GrantRequestCreateRequest): Promise<unknown> {
        return aki(PamApi)
            .pamGrantRequestsCreate({
                grantRequestCreateRequest: {
                    pbms: [
                        ...this.selectedApps.map((app) => app.pbmUuid),
                        ...this.selectedEntitlements.map((entitlement) => entitlement.pbmUuid),
                    ],
                },
            })
            .then((v) => {
                window.location.assign(v.link);
            });
    }

    private entitlementsForApp(app: Application): RequestableTarget[] {
        return (this.entitlements ?? []).filter(
            (entitlement) => entitlement.parent.pbmUuid === app.pbmUuid,
        );
    }

    private toggleApp(app: Application) {
        const idx = this.selectedApps.indexOf(app);
        if (idx > -1) {
            this.selectedApps.splice(idx, 1);
        } else {
            this.selectedApps.push(app);
        }
        this.requestUpdate();
    }

    private toggleEntitlement(entitlement: RequestableTarget) {
        const idx = this.selectedEntitlements.indexOf(entitlement);
        if (idx > -1) {
            this.selectedEntitlements.splice(idx, 1);
        } else {
            this.selectedEntitlements.push(entitlement);
        }
        this.requestUpdate();
    }

    protected renderForm(): SlottedTemplateResult | null {
        // Every app with its own request rule, plus every app that only has requestable
        // entitlements underneath it (and so never got its own card via `apps`).
        const apps = [...(this.apps?.results ?? [])];
        const knownAppPbms = new Set(apps.map((app) => app.pbmUuid));
        for (const entitlement of this.entitlements ?? []) {
            if (!knownAppPbms.has(entitlement.parent.pbmUuid)) {
                knownAppPbms.add(entitlement.parent.pbmUuid);
                apps.push(entitlement.parent);
            }
        }

        return html`<div class="pf-l-grid pf-m-gutter">
            ${apps.map((app) => {
                const appIsRequestable = this.apps?.results.includes(app) ?? false;
                const entitlements = this.entitlementsForApp(app);
                return html`
                    <div
                        class="pf-l-grid__item pf-m-2-col pf-c-card pf-m-compact ${appIsRequestable
                            ? "pf-m-selectable-raised"
                            : ""} ${this.selectedApps.includes(app) ? "pf-m-selected-raised" : ""}"
                    >
                        <div
                            @click=${() => {
                                if (appIsRequestable) {
                                    this.toggleApp(app);
                                }
                            }}
                        >
                            <ak-app-icon
                                exportparts="icon:card-header-icon"
                                size=${PFSize.Large}
                                name=${app.name}
                                icon=${ifPresent(app.metaIconUrl)}
                                .iconThemedUrls=${app.metaIconThemedUrls}
                            ></ak-app-icon>
                            <div role="heading" aria-level="2" class="pf-c-card__title">
                                ${app.name}
                            </div>
                        </div>
                        ${entitlements.length > 0
                            ? html`<div class="ak-requestable-entitlements">
                                  ${entitlements.map((entitlement) => {
                                      const id = `entitlement-${entitlement.pbmUuid}`;
                                      return html`<div class="pf-c-check">
                                          <input
                                              type="checkbox"
                                              class="pf-c-check__input"
                                              id=${id}
                                              ?checked=${this.selectedEntitlements.includes(
                                                  entitlement,
                                              )}
                                              @change=${() => this.toggleEntitlement(entitlement)}
                                          />
                                          <label class="pf-c-check__label" for=${id}
                                              >${entitlement.label}</label
                                          >
                                      </div>`;
                                  })}
                              </div>`
                            : nothing}
                    </div>
                `;
            })}
        </div> `;
    }
}
