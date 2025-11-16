import "#components/ak-status-label";
import "#admin/endpoints/devices/BoundDeviceUsersList";

import { DEFAULT_CONFIG } from "#common/api/config";
import { APIError, parseAPIResponseError } from "#common/errors/network";

import { AKElement } from "#elements/Base";
import { Timestamp } from "#elements/table/shared";

import { setPageDetails } from "#components/ak-page-navbar";
import renderDescriptionList from "#components/DescriptionList";

import { Disk, EndpointDevice, EndpointsApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

function getSize(size: number) {
    const sizes = [" Bytes", " KB", " MB", " GB", " TB", " PB", " EB", " ZB", " YB"];

    for (let i = 1; i < sizes.length; i++) {
        if (size < Math.pow(1024, i))
            return Math.round((size / Math.pow(1024, i - 1)) * 100) / 100 + sizes[i - 1];
    }
    return size.toString();
}

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
            header: this.device?.facts.network?.hostname ?? msg("Loading device..."),
            description: this.device?.facts.os?.name + " " + this.device?.facts.os?.version,
        });
    }

    render() {
        if (!this.device) {
            return nothing;
        }
        const _rootDisk = this.device.facts.disks?.filter((d) => d.mountpoint === "/") || [];
        let rootDisk: Disk | undefined = undefined;
        if (_rootDisk?.length > 0) {
            rootDisk = _rootDisk[0];
        }
        return html`<section class="pf-c-page__main-section">
            <div class="pf-l-grid pf-m-gutter">
                <div class="pf-l-grid__item pf-m-4-col pf-c-card">
                    <div class="pf-c-card__title">${msg("Device details")}</div>
                    <div class="pf-c-card__body">
                        ${renderDescriptionList(
                            [
                                [msg("Name"), this.device.facts.network?.hostname],
                                [msg("Serial number"), this.device.facts.hardware?.serial],
                                [
                                    msg("Operating system"),
                                    [
                                        this.device.facts.os?.name,
                                        this.device.facts.os?.version,
                                    ].join(" "),
                                ],
                                [
                                    msg("Disk encryption"),
                                    html`<ak-status-label
                                        ?good=${rootDisk?.encryptionEnabled}
                                    ></ak-status-label>`,
                                ],
                                [
                                    msg("Firewall enabled"),
                                    html`<ak-status-label
                                        ?good=${this.device.facts.network?.firewallEnabled}
                                    ></ak-status-label>`,
                                ],
                            ],
                            { horizontal: true },
                        )}
                    </div>
                </div>
                <div class="pf-l-grid__item pf-m-4-col pf-c-card">
                    <div class="pf-c-card__title">${msg("Hardware")}</div>
                    <div class="pf-c-card__body">
                        ${renderDescriptionList(
                            [
                                [msg("Manufacturer"), this.device.facts.hardware?.manufacturer],
                                [msg("Model"), this.device.facts.hardware?.model],
                                [
                                    msg("CPU"),
                                    msg(
                                        str`${this.device.facts.hardware?.cpuCount} x ${this.device.facts.hardware?.cpuName}`,
                                    ),
                                ],
                                [
                                    msg("Memory"),
                                    this.device.facts.hardware?.memoryBytes
                                        ? getSize(this.device.facts.hardware?.memoryBytes)
                                        : "-",
                                ],
                                [
                                    msg("Disk usage"),
                                    rootDisk?.capacityTotalBytes && rootDisk.capacityUsedBytes
                                        ? html`<progress
                                              value="${rootDisk.capacityUsedBytes}"
                                              max="${rootDisk.capacityTotalBytes}"
                                          ></progress>`
                                        : "-",
                                ],
                            ],
                            { horizontal: true },
                        )}
                    </div>
                </div>
                <div class="pf-l-grid__item pf-m-4-col pf-c-card">
                    <div class="pf-c-card__title">${msg("Connections")}</div>
                    <div class="pf-c-card__body">
                        <dl class="pf-c-description-list pf-m-horizontal">
                            ${this.device.connectionsObj.map((conn) => {
                                return html`<div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text"
                                            >${conn.connectorObj.name}</span
                                        >
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            ${conn.latestSnapshot?.created
                                                ? Timestamp(conn.latestSnapshot.created)
                                                : html`-`}
                                        </div>
                                    </dd>
                                </div>`;
                            })}
                        </dl>
                    </div>
                </div>
                <div class="pf-l-grid__item pf-m-6-col pf-c-card">
                    <div class="pf-c-card__title">${msg("Users / Groups")}</div>
                    <div class="pf-c-card__body">
                        <ak-bound-device-users-list
                            .target=${this.device.pbmUuid}
                        ></ak-bound-device-users-list>
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
