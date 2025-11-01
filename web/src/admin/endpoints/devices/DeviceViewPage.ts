import { DEFAULT_CONFIG } from "#common/api/config";
import { APIError, parseAPIResponseError } from "#common/errors/network";

import { AKElement } from "#elements/Base";

import { setPageDetails } from "#components/ak-page-navbar";

import { EndpointDevice, EndpointsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

@customElement("ak-endpoints-device-view")
export class DeviceViewPage extends AKElement {
    @property({ type: String })
    public deviceId?: string;

    @state()
    protected device?: EndpointDevice;

    @state()
    protected error?: APIError;

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
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-device-view": DeviceViewPage;
    }
}
