import "#components/ak-status-label";
import "#admin/endpoints/devices/BoundDeviceUsersList";
import "#admin/endpoints/devices/facts/DeviceProcessTable";
import "#admin/endpoints/devices/facts/DeviceUserTable";
import "#admin/endpoints/devices/facts/DeviceGroupTable";
import "#admin/endpoints/devices/DeviceForm";
import "#elements/forms/ModalForm";
import "#elements/Tabs";

import { DEFAULT_CONFIG } from "#common/api/config";
import { APIError, parseAPIResponseError } from "#common/errors/network";

import { AKElement } from "#elements/Base";
import { Timestamp } from "#elements/table/shared";

import { setPageDetails } from "#components/ak-page-navbar";
import renderDescriptionList from "#components/DescriptionList";

import { getSize } from "#admin/endpoints/devices/utils";

import { Disk, EndpointDeviceDetails, EndpointsApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

@customElement("ak-endpoints-device-view")
export class DeviceViewPage extends AKElement {
    @property({ type: String })
    public deviceId?: string;

    @state()
    protected device?: EndpointDeviceDetails;

    @state()
    protected error?: APIError;

    static styles: CSSResult[] = [PFCard, PFPage, PFGrid, PFButton, PFDescriptionList];

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
            header: this.device?.name
                ? msg(str`Device ${this.device?.name}`)
                : msg("Loading device..."),
            description: this.device?.facts.data.os
                ? this.device?.facts.data.os?.name + " " + this.device?.facts.data.os?.version
                : undefined,
            icon: "fa fa-laptop",
        });
    }

    renderOverview() {
        if (!this.device) {
            return nothing;
        }
        const _rootDisk =
            this.device.facts.data.disks?.filter(
                (d) => d.mountpoint === "/" || d.mountpoint === "C:",
            ) || [];
        let rootDisk: Disk | undefined = undefined;
        if (_rootDisk?.length > 0) {
            rootDisk = _rootDisk[0];
        }
        return html`<div class="pf-l-grid pf-m-gutter">
            <div class="pf-l-grid__item pf-m-4-col pf-c-card">
                <div class="pf-c-card__title">${msg("Device details")}</div>
                <div class="pf-c-card__body">
                    ${renderDescriptionList(
                        [
                            [msg("Name"), this.device.name],
                            [msg("Hostname"), this.device.facts.data.network?.hostname ?? "-"],
                            [msg("Serial number"), this.device.facts.data.hardware?.serial ?? "-"],
                            [
                                msg("Operating system"),
                                this.device.facts.data.os
                                    ? [
                                          this.device.facts.data.os?.name,
                                          this.device.facts.data.os?.version,
                                      ].join(" ")
                                    : "-",
                            ],
                            [
                                msg("Firewall enabled"),
                                html`<ak-status-label
                                    ?good=${this.device.facts.data.network?.firewallEnabled}
                                ></ak-status-label>`,
                            ],
                            [msg("Group"), this.device.accessGroupObj?.name ?? "-"],
                            [
                                msg("Actions"),
                                html`<ak-forms-modal>
                                    <span slot="submit">${msg("Update")}</span>
                                    <span slot="header">${msg("Update Device")}</span>
                                    <ak-endpoints-device-form
                                        slot="form"
                                        .instancePk=${this.device.deviceUuid}
                                    >
                                    </ak-endpoints-device-form>
                                    <button slot="trigger" class="pf-c-button pf-m-primary">
                                        ${msg("Edit")}
                                    </button>
                                </ak-forms-modal>`,
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
                            [
                                msg("Manufacturer"),
                                this.device.facts.data.hardware?.manufacturer ?? "-",
                            ],
                            [msg("Model"), this.device.facts.data.hardware?.model ?? "-"],
                            [
                                msg("CPU"),
                                this.device.facts.data.hardware
                                    ? msg(
                                          str`${this.device.facts.data.hardware?.cpuCount} x ${this.device.facts.data.hardware?.cpuName}`,
                                      )
                                    : "-",
                            ],
                            [
                                msg("Memory"),
                                this.device.facts.data.hardware?.memoryBytes
                                    ? getSize(this.device.facts.data.hardware?.memoryBytes)
                                    : "-",
                            ],
                            [
                                msg("Disk encryption"),
                                html`<ak-status-label
                                    ?good=${rootDisk?.encryptionEnabled}
                                ></ak-status-label>`,
                            ],
                            [
                                msg("Disk size"),
                                rootDisk?.capacityTotalBytes
                                    ? getSize(rootDisk.capacityTotalBytes)
                                    : "-",
                            ],
                            [
                                msg("Disk usage"),
                                rootDisk?.capacityTotalBytes && rootDisk.capacityUsedBytes
                                    ? html`<progress
                                              value="${rootDisk.capacityUsedBytes}"
                                              max="${rootDisk.capacityTotalBytes}"
                                          ></progress>
                                          ${Math.round(
                                              (rootDisk.capacityUsedBytes * 100) /
                                                  rootDisk.capacityTotalBytes,
                                          )}%`
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
            <div class="pf-l-grid__item pf-m-12-col pf-c-card">
                <div class="pf-c-card__title">${msg("Users / Groups")}</div>
                <div class="pf-c-card__body">
                    <ak-bound-device-users-list
                        .target=${this.device.pbmUuid}
                    ></ak-bound-device-users-list>
                </div>
            </div>
        </div>`;
    }

    renderProcesses() {
        if (!this.device) {
            return nothing;
        }
        return html`<ak-endpoints-device-process-table
            .device=${this.device}
        ></ak-endpoints-device-process-table>`;
    }

    renderUsers() {
        if (!this.device) {
            return nothing;
        }
        return html`<ak-endpoints-device-users-table
            .device=${this.device}
        ></ak-endpoints-device-users-table>`;
    }

    renderGroups() {
        if (!this.device) {
            return nothing;
        }
        return html`<ak-endpoints-device-groups-table
            .device=${this.device}
        ></ak-endpoints-device-groups-table>`;
    }

    render() {
        return html`<main part="main">
            <ak-tabs part="tabs">
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-overview"
                    id="page-overview"
                    aria-label="${msg("Overview")}"
                    class="pf-c-page__main-section"
                >
                    ${this.renderOverview()}
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-processes"
                    id="page-processes"
                    aria-label="${msg("Processes")}"
                    class="pf-c-page__main-section"
                >
                    ${this.renderProcesses()}
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-users"
                    id="page-users"
                    aria-label="${msg("Users")}"
                    class="pf-c-page__main-section"
                >
                    ${this.renderUsers()}
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-groups"
                    id="page-groups"
                    aria-label="${msg("Groups")}"
                    class="pf-c-page__main-section"
                >
                    ${this.renderGroups()}
                </div>
            </ak-tabs>
        </main>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-device-view": DeviceViewPage;
    }
}
