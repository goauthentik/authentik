import "#elements/EmptyState";
import "#elements/timestamp/ak-timestamp";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFTable from "@patternfly/patternfly/components/Table/table.css";

import { aki } from "#common/api/client";

import { AKElement } from "#elements/Base";

import {
    ProvidersApi,
    SCIMResourceType,
    SCIMResourceTypeDiscovery,
    SCIMResourceTypeDiscoveryStatusEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

@customElement("ak-provider-scim-resource-types")
export class SCIMResourceTypesCard extends AKElement {
    @property({ type: Number })
    providerID?: number;

    @state()
    protected result?: SCIMResourceTypeDiscovery;

    @state()
    protected loading = false;

    @state()
    protected error = false;

    @state()
    protected queried = false;

    private requestVersion = 0;

    static styles: CSSResult[] = [
        PFButton,
        PFCard,
        PFContent,
        PFTable,
        css`
            .results {
                overflow-x: auto;
            }
            td {
                overflow-wrap: anywhere;
            }
            details {
                margin-top: 0.5rem;
            }
        `,
    ];

    willUpdate(changed: PropertyValues<this>) {
        if (changed.has("providerID")) {
            this.requestVersion++;
            this.result = undefined;
            this.error = false;
            this.loading = false;
            this.queried = false;
        }
    }

    async fetchResourceTypes() {
        if (!this.providerID || this.loading) return;
        const version = ++this.requestVersion;
        const id = this.providerID;
        const refresh = this.queried;
        this.queried = true;
        this.loading = true;
        this.error = false;
        this.result = undefined;

        try {
            const result = await aki(ProvidersApi).providersScimResourceTypesRetrieve({
                id,
                refresh,
            });

            if (version === this.requestVersion && id === this.providerID) {
                this.result = result;
            }
        } catch {
            if (version === this.requestVersion && id === this.providerID) {
                this.error = true;
            }
        } finally {
            if (version === this.requestVersion && id === this.providerID) {
                this.loading = false;
            }
        }
    }

    private renderResource(resource: SCIMResourceType): TemplateResult {
        return html`<tr>
            <td>
                ${resource.name}
                <details>
                    <summary>
                        ${msg("Details", { id: "scim.resource-types.details.label" })}
                    </summary>
                    ${
                        resource.id
                            ? html`<p>
                                  ${msg("ID", { id: "scim.resource-types.id.label" })}:
                                  ${resource.id}
                              </p>`
                            : nothing
                    }
                    ${resource.description ? html`<p>${resource.description}</p>` : nothing}
                    <p>
                        ${msg("Schema extensions", {
                            id: "scim.resource-types.extensions.label",
                        })}
                    </p>
                    ${
                        resource.schemaExtensions.length
                            ? html`<ul>
                                  ${resource.schemaExtensions.map(
                                      (extension) =>
                                          html`<li>
                                              <code>${extension.schema}</code>
                                              (${
                                                  extension.required
                                                      ? msg("Required", {
                                                            id: "scim.resource-types.extension-required.label",
                                                        })
                                                      : msg("Optional", {
                                                            id: "scim.resource-types.extension-optional.label",
                                                        })
                                              })
                                          </li>`,
                                  )}
                              </ul>`
                            : html`<p>
                                  ${msg("None advertised", {
                                      id: "scim.resource-types.no-extensions.label",
                                  })}
                              </p>`
                    }
                </details>
            </td>
            <td><code>${resource.endpoint}</code></td>
            <td><code>${resource.schema}</code></td>
        </tr>`;
    }

    private renderResult() {
        if (this.loading) {
            return html`<ak-empty-state loading></ak-empty-state>`;
        }

        if (this.error) {
            return html`<p role="alert">
                ${msg("Unable to load resource-type diagnostics. Try again.", {
                    id: "scim.resource-types.request.error",
                })}
            </p>`;
        }

        if (!this.result) {
            return html`<p>
                ${msg("Not queried. Fetch resource types to inspect the destination.", {
                    id: "scim.resource-types.not-queried.description",
                })}
            </p>`;
        }

        const result = this.result;

        const status = {
            [SCIMResourceTypeDiscoveryStatusEnum.Success]: msg("Successful", {
                id: "scim.resource-types.success.label",
            }),
            [SCIMResourceTypeDiscoveryStatusEnum.Unavailable]: msg("Unavailable", {
                id: "scim.resource-types.unavailable.label",
            }),
            [SCIMResourceTypeDiscoveryStatusEnum.Error]: msg("Failed", {
                id: "scim.resource-types.failed.label",
            }),
            [SCIMResourceTypeDiscoveryStatusEnum.UnknownDefaultOpenApi]: msg("Unknown", {
                id: "scim.resource-types.unknown.label",
            }),
        }[result.status];

        return html`
            <p>${msg("Discovery", { id: "scim.resource-types.discovery.label" })}: ${status}</p>
            <p>
                ${msg("Last checked", { id: "scim.resource-types.last-checked.label" })}:
                <ak-timestamp .timestamp=${result.fetchedAt}></ak-timestamp>
                ${
                    result.cached
                        ? msg("(cached)", { id: "scim.resource-types.cached.label" })
                        : nothing
                }
            </p>
            ${result.detail ? html`<p>${result.detail}</p>` : nothing}
            ${
                result.status === SCIMResourceTypeDiscoveryStatusEnum.Success
                    ? result.resourceTypes.length
                        ? html`<div class="results">
                              <table class="pf-c-table pf-m-compact">
                                  <caption>
                                      ${msg("Advertised resource types", {
                                          id: "scim.resource-types.title.label",
                                      })}
                                  </caption>
                                  <thead>
                                      <tr>
                                          <th scope="col">
                                              ${msg("Name", { id: "scim.resource-types.name.label" })}
                                          </th>
                                          <th scope="col">
                                              ${msg("Endpoint", {
                                                  id: "scim.resource-types.endpoint.label",
                                              })}
                                          </th>
                                          <th scope="col">
                                              ${msg("Schema", {
                                                  id: "scim.resource-types.schema.label",
                                              })}
                                          </th>
                                      </tr>
                                  </thead>
                                  <tbody>
                                      ${result.resourceTypes.map((resource) =>
                                          this.renderResource(resource),
                                      )}
                                  </tbody>
                              </table>
                          </div>`
                        : html`<p>
                              ${msg("The destination advertised no resource types.", {
                                  id: "scim.resource-types.empty.description",
                              })}
                          </p>`
                    : nothing
            }
        `;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-card">
            <div class="pf-c-card__header">
                <div class="pf-c-card__actions">
                    <button
                        class="pf-c-button pf-m-secondary"
                        type="button"
                        ?disabled=${this.loading || !this.providerID}
                        @click=${() => this.fetchResourceTypes()}
                    >
                        ${
                            this.queried
                                ? msg("Refresh", { id: "scim.resource-types.refresh.label" })
                                : msg("Fetch resource types", {
                                      id: "scim.resource-types.fetch.label",
                                  })
                        }
                    </button>
                </div>
                <h2 class="pf-c-card__title">
                    ${msg("Advertised resource types", { id: "scim.resource-types.title.label" })}
                </h2>
            </div>
            <div class="pf-c-card__body pf-c-content">
                <p>
                    ${msg(
                        "Inspect the destination's ResourceTypes response. This diagnostic does not change synchronization behavior.",
                        { id: "scim.resource-types.purpose.description" },
                    )}
                </p>
                <div aria-live="polite" aria-busy=${this.loading}>${this.renderResult()}</div>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-scim-resource-types": SCIMResourceTypesCard;
    }
}
