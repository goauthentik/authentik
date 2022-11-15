import { UserMatchingModeToLabel } from "@goauthentik/admin/sources/oauth/utils";
import { DEFAULT_CONFIG, config } from "@goauthentik/common/api/config";
import { PlexAPIClient, PlexResource, popupCenterScreen } from "@goauthentik/common/helpers/plex";
import { first, randomString } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import {
    CapabilitiesEnum,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    PlexSource,
    SourcesApi,
    UserMatchingModeEnum,
} from "@goauthentik/api";

@customElement("ak-source-plex-form")
export class PlexSourceForm extends ModelForm<PlexSource, string> {
    loadInstance(pk: string): Promise<PlexSource> {
        return new SourcesApi(DEFAULT_CONFIG)
            .sourcesPlexRetrieve({
                slug: pk,
            })
            .then((source) => {
                this.plexToken = source.plexToken;
                this.loadServers();
                return source;
            });
    }

    @state()
    clearIcon = false;

    @property()
    plexToken?: string;

    @property({ attribute: false })
    plexResources?: PlexResource[];

    get defaultInstance(): PlexSource | undefined {
        return {
            clientId: randomString(40),
        } as PlexSource;
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated source.`;
        } else {
            return t`Successfully created source.`;
        }
    }

    send = async (data: PlexSource): Promise<PlexSource> => {
        data.plexToken = this.plexToken || "";
        let source: PlexSource;
        if (this.instance) {
            source = await new SourcesApi(DEFAULT_CONFIG).sourcesPlexUpdate({
                slug: this.instance.slug,
                plexSourceRequest: data,
            });
        } else {
            source = await new SourcesApi(DEFAULT_CONFIG).sourcesPlexCreate({
                plexSourceRequest: data,
            });
        }
        const c = await config();
        if (c.capabilities.includes(CapabilitiesEnum.SaveMedia)) {
            const icon = this.getFormFiles()["icon"];
            if (icon || this.clearIcon) {
                await new SourcesApi(DEFAULT_CONFIG).sourcesAllSetIconCreate({
                    slug: source.slug,
                    file: icon,
                    clear: this.clearIcon,
                });
            }
        } else {
            await new SourcesApi(DEFAULT_CONFIG).sourcesAllSetIconUrlCreate({
                slug: source.slug,
                filePathRequest: {
                    url: data.icon || "",
                },
            });
        }
        return source;
    };

    async doAuth(): Promise<void> {
        const authInfo = await PlexAPIClient.getPin(this.instance?.clientId || "");
        const authWindow = popupCenterScreen(authInfo.authUrl, "plex auth", 550, 700);
        PlexAPIClient.pinPoll(this.instance?.clientId || "", authInfo.pin.id).then((token) => {
            authWindow?.close();
            this.plexToken = token;
            this.loadServers();
        });
    }

    async loadServers(): Promise<void> {
        if (!this.plexToken) {
            return;
        }
        this.plexResources = await new PlexAPIClient(this.plexToken).getServers();
    }

    renderSettings(): TemplateResult {
        if (!this.plexToken) {
            return html` <button
                class="pf-c-button pf-m-primary"
                type="button"
                @click=${() => {
                    this.doAuth();
                }}
            >
                ${t`Load servers`}
            </button>`;
        }
        return html` <button
                class="pf-c-button pf-m-secondary"
                type="button"
                @click=${() => {
                    this.doAuth();
                }}
            >
                ${t`Re-authenticate with plex`}
            </button>
            <ak-form-element-horizontal name="allowFriends">
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.allowFriends, true)}
                    />
                    <label class="pf-c-check__label">
                        ${t`Allow friends to authenticate via Plex, even if you don't share any servers`}
                    </label>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Allowed servers`}
                ?required=${true}
                name="allowedServers"
            >
                <select class="pf-c-form-control" multiple>
                    ${this.plexResources?.map((r) => {
                        const selected = Array.from(this.instance?.allowedServers || []).some(
                            (server) => {
                                return server == r.clientIdentifier;
                            },
                        );
                        return html`<option value=${r.clientIdentifier} ?selected=${selected}>
                            ${r.name}
                        </option>`;
                    })}
                </select>
                <p class="pf-c-form__helper-text">
                    ${t`Select which server a user has to be a member of to be allowed to authenticate.`}
                </p>
                <p class="pf-c-form__helper-text">
                    ${t`Hold control/command to select multiple items.`}
                </p>
            </ak-form-element-horizontal>`;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Slug`} ?required=${true} name="slug">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.slug)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="enabled">
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.enabled, true)}
                    />
                    <label class="pf-c-check__label"> ${t`Enabled`} </label>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`User matching mode`}
                ?required=${true}
                name="userMatchingMode"
            >
                <select class="pf-c-form-control">
                    <option
                        value=${UserMatchingModeEnum.Identifier}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.Identifier}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.Identifier)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.EmailLink}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.EmailLink}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.EmailLink)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.EmailDeny}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.EmailDeny}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.EmailDeny)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.UsernameLink}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.UsernameLink}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.UsernameLink)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.UsernameDeny}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.UsernameDeny}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.UsernameDeny)}
                    </option>
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`User path`} name="userPathTemplate">
                <input
                    type="text"
                    value="${first(
                        this.instance?.userPathTemplate,
                        "goauthentik.io/sources/%(slug)s",
                    )}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${t`Path template for users created. Use placeholders like \`%(slug)s\` to insert the source slug.`}
                </p>
            </ak-form-element-horizontal>
            ${until(
                config().then((c) => {
                    if (c.capabilities.includes(CapabilitiesEnum.SaveMedia)) {
                        return html`<ak-form-element-horizontal label=${t`Icon`} name="icon">
                                <input type="file" value="" class="pf-c-form-control" />
                                ${this.instance?.icon
                                    ? html`
                                          <p class="pf-c-form__helper-text">
                                              ${t`Currently set to:`} ${this.instance?.icon}
                                          </p>
                                      `
                                    : html``}
                            </ak-form-element-horizontal>
                            ${this.instance?.icon
                                ? html`
                                      <ak-form-element-horizontal>
                                          <div class="pf-c-check">
                                              <input
                                                  type="checkbox"
                                                  class="pf-c-check__input"
                                                  @change=${(ev: Event) => {
                                                      const target = ev.target as HTMLInputElement;
                                                      this.clearIcon = target.checked;
                                                  }}
                                              />
                                              <label class="pf-c-check__label">
                                                  ${t`Clear icon`}
                                              </label>
                                          </div>
                                          <p class="pf-c-form__helper-text">
                                              ${t`Delete currently set icon.`}
                                          </p>
                                      </ak-form-element-horizontal>
                                  `
                                : html``}`;
                    }
                    return html`<ak-form-element-horizontal label=${t`Icon`} name="icon">
                        <input
                            type="text"
                            value="${first(this.instance?.icon, "")}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Either input a full URL, a relative path, or use 'fa://fa-test' to use the Font Awesome icon "fa-test".`}
                        </p>
                    </ak-form-element-horizontal>`;
                }),
            )}

            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Protocol settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Client ID`}
                        ?required=${true}
                        name="clientId"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.clientId, "")}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                    ${this.renderSettings()}
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header"> ${t`Flow settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Authentication flow`}
                        ?required=${true}
                        name="authenticationFlow"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value=""
                                ?selected=${this.instance?.authenticationFlow === undefined}
                            >
                                ---------
                            </option>
                            ${until(
                                new FlowsApi(DEFAULT_CONFIG)
                                    .flowsInstancesList({
                                        ordering: "slug",
                                        designation:
                                            FlowsInstancesListDesignationEnum.Authentication,
                                    })
                                    .then((flows) => {
                                        return flows.results.map((flow) => {
                                            let selected =
                                                this.instance?.authenticationFlow === flow.pk;
                                            if (
                                                !this.instance?.pk &&
                                                !this.instance?.authenticationFlow &&
                                                flow.slug === "default-source-authentication"
                                            ) {
                                                selected = true;
                                            }
                                            return html`<option
                                                value=${ifDefined(flow.pk)}
                                                ?selected=${selected}
                                            >
                                                ${flow.name} (${flow.slug})
                                            </option>`;
                                        });
                                    }),
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${t`Flow to use when authenticating existing users.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Enrollment flow`}
                        ?required=${true}
                        name="enrollmentFlow"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value=""
                                ?selected=${this.instance?.enrollmentFlow === undefined}
                            >
                                ---------
                            </option>
                            ${until(
                                new FlowsApi(DEFAULT_CONFIG)
                                    .flowsInstancesList({
                                        ordering: "slug",
                                        designation: FlowsInstancesListDesignationEnum.Enrollment,
                                    })
                                    .then((flows) => {
                                        return flows.results.map((flow) => {
                                            let selected =
                                                this.instance?.enrollmentFlow === flow.pk;
                                            if (
                                                !this.instance?.pk &&
                                                !this.instance?.enrollmentFlow &&
                                                flow.slug === "default-source-enrollment"
                                            ) {
                                                selected = true;
                                            }
                                            return html`<option
                                                value=${ifDefined(flow.pk)}
                                                ?selected=${selected}
                                            >
                                                ${flow.name} (${flow.slug})
                                            </option>`;
                                        });
                                    }),
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${t`Flow to use when enrolling new users.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
