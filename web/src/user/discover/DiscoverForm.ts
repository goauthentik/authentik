import "../../elements/AppIcon";

import { aki } from "#common/api/client";
import { PFSize } from "#common/enums";

import { Form } from "#elements/forms/Form";
import { PaginatedResponse } from "#elements/table/shared";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { Application, CoreApi, GrantRequestCreateRequest, PamApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css } from "lit";
import { html } from "lit-html";
import { customElement, state } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

@customElement("ak-discover-form")
export class DiscoverForm extends Form<GrantRequestCreateRequest> {
    public static override createLabel = null;
    public static submitVerb: string = msg("Request");

    static styles = [
        ...super.styles,
        PFCard,
        PFGrid,
        css`
            .pf-l-grid {
                padding: 1rem 0;
            }
        `,
    ];

    @state()
    apps?: PaginatedResponse<Application>;

    @state()
    selected: Application[] = [];

    public override async connectedCallback(): Promise<void> {
        super.connectedCallback();

        this.apps = await aki(CoreApi).coreApplicationsRequestableList({});
    }

    protected send(_data: GrantRequestCreateRequest): Promise<unknown> {
        return aki(PamApi)
            .pamGrantRequestsCreate({
                grantRequestCreateRequest: {
                    pbms: this.selected.map((a) => a.pbmUuid),
                },
            })
            .then((v) => {
                window.location.assign(v.link);
            });
    }

    protected renderForm(): SlottedTemplateResult | null {
        return html`<div class="pf-l-grid pf-m-gutter">
            ${this.apps?.results.map((app) => {
                return html`
                    <div
                        class="pf-l-grid__item pf-m-2-col pf-c-card pf-m-selectable-raised pf-m-compact ${this.selected.includes(
                            app,
                        )
                            ? "pf-m-selected-raised"
                            : ""}"
                        @click=${() => {
                            if (this.selected.includes(app)) {
                                this.selected.splice(this.selected.indexOf(app), 1);
                            } else {
                                this.selected.push(app);
                            }
                            this.requestUpdate();
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
                `;
            })}
        </div> `;
    }
}
