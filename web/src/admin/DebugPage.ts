import { DEFAULT_CONFIG } from "#common/api/config";
import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { MessageLevel } from "#common/messages";
import "#components/ak-page-header";
import { AKElement } from "#elements/Base";
import { showMessage } from "#elements/messages/MessageContainer";
import * as Sentry from "@sentry/browser";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { AdminApi } from "@goauthentik/api";

@customElement("ak-admin-debug-page")
export class DebugPage extends AKElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFCard, PFPage, PFGrid, PFButton];
    }

    render(): TemplateResult {
        return html`
            <ak-page-header icon="pf-icon pf-icon-user" header="Debug"> </ak-page-header>
            <section class="pf-c-page__main-section">
                <div class="pf-l-grid pf-m-gutter">
                    <div class="pf-l-grid__item pf-m-3-col pf-c-card">
                        <div class="pf-c-card__title">Sentry</div>
                        <div class="pf-c-card__body">
                            <button
                                class="pf-c-button pf-m-primary"
                                @click=${() => {
                                    Sentry.captureException(new Error("test error"));
                                }}
                            >
                                Send test error
                            </button>
                        </div>
                    </div>
                    <div class="pf-l-grid__item pf-m-3-col pf-c-card">
                        <div class="pf-c-card__title">Misc</div>
                        <div class="pf-c-card__body">
                            <button
                                class="pf-c-button pf-m-primary"
                                @click=${() => {
                                    new AdminApi(DEFAULT_CONFIG)
                                        .adminSystemCreate()
                                        .then(() => {
                                            showMessage({
                                                level: MessageLevel.success,
                                                message: "Success",
                                            });
                                        })
                                        .catch(async (error) => {
                                            const parsedError = await parseAPIResponseError(error);

                                            showMessage({
                                                level: MessageLevel.error,
                                                message: pluckErrorDetail(parsedError),
                                            });
                                        });
                                }}
                            >
                                POST System
                            </button>
                        </div>
                    </div>
                </div>
            </section>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-debug-page": DebugPage;
    }
}
