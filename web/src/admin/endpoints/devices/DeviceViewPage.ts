import { DEFAULT_CONFIG } from "#common/api/config";
import { APIError, parseAPIResponseError } from "#common/errors/network";

import { AKElement } from "#elements/Base";

import { setPageDetails } from "#components/ak-page-navbar";

import { EndpointDevice, EndpointsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-endpoints-device-view")
export class DeviceViewPage extends AKElement {
    @property({ type: String })
    public deviceId?: string;

    @state()
    protected device?: EndpointDevice;

    @state()
    protected error?: APIError;

    static styles: CSSResult[] = [PFBase, PFCard, PFPage, PFGrid, PFButton, PFDescriptionList];

    protected fetchDevice(id: string) {
        new EndpointsApi(DEFAULT_CONFIG)
            .endpointsDevicesRetrieve({ deviceUuid: id })
            .then((dev) => {
                this.device = dev;
            })
            .catch(async (error) => {
                this.error = await parseAPIResponseError(error);
            });
    }

    public override willUpdate(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("deviceId") && this.deviceId) {
            this.fetchDevice(this.deviceId);
        }
    }

    updated(changed: PropertyValues<this>) {
        super.updated(changed);
        setPageDetails({
            header: this.device?.data.network?.hostname ?? msg("Loading device..."),
            description: this.device?.data.os?.version,
        });
    }

    render() {
        return html`<section class="pf-c-page__main-section">
            <div class="pf-l-grid pf-m-gutter">
                <div class="pf-l-grid__item pf-m-3-col pf-c-card">
                    <div class="pf-c-card__body">
                        <dl class="pf-c-description-list pf-m-horizontal">
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text">${msg("Name")}</span>
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        ${this.device?.data.network?.hostname}
                                    </div>
                                </dd>
                            </div>

                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text"
                                        >${msg("Serial")}</span
                                    >
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        ${this.device?.data.hardware?.serial}
                                    </div>
                                </dd>
                            </div>
                        </dl>
                    </div>
                </div>
            </div>
        </section>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-device-view": DeviceViewPage;
    }
}
