import "#components/ak-text-input";
import "#components/ak-textarea-input";

import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";

import { StagesApi, WebAuthnRPConfig } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-authenticator-webauthn-rp-config-form")
export class WebAuthnRPConfigForm extends ModelForm<WebAuthnRPConfig, string> {
    public static override verboseName = msg("WebAuthn RP Config", {
        id: "webauthn-rp-config.verbose-name",
    });
    public static override verboseNamePlural = msg("WebAuthn RP Configs", {
        id: "webauthn-rp-config.verbose-name-plural",
    });

    #stagesAPI = aki(StagesApi);

    loadInstance(pk: string): Promise<WebAuthnRPConfig> {
        return this.#stagesAPI.stagesAuthenticatorWebauthnRpConfigsRetrieve({
            rpConfigUuid: pk,
        });
    }

    public override getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated WebAuthn RP config.", {
                  id: "webauthn-rp-config.form.success.updated",
              })
            : msg("Successfully created WebAuthn RP config.", {
                  id: "webauthn-rp-config.form.success.created",
              });
    }

    protected override async send(data: WebAuthnRPConfig): Promise<WebAuthnRPConfig> {
        data.origins = (data.origins as unknown as string)
            .split("\n")
            .map((origin) => origin.trim())
            .filter(Boolean);

        if (this.instance?.rpConfigUuid) {
            return this.#stagesAPI.stagesAuthenticatorWebauthnRpConfigsPartialUpdate({
                rpConfigUuid: this.instance.rpConfigUuid,
                patchedWebAuthnRPConfigRequest: data,
            });
        }

        return this.#stagesAPI.stagesAuthenticatorWebauthnRpConfigsCreate({
            webAuthnRPConfigRequest: data,
        });
    }

    protected override renderForm(): TemplateResult {
        return html`<ak-text-input
                required
                name="name"
                value="${this.instance?.name ?? ""}"
                label=${msg("Name", { id: "webauthn-rp-config.form.name.label" })}
                ?autofocus=${!this.instance}
            ></ak-text-input>

            <ak-text-input
                required
                name="rpId"
                input-hint="code"
                placeholder="sso.example.com"
                value="${this.instance?.rpId ?? ""}"
                label=${msg("RP ID", { id: "webauthn-rp-config.form.rp-id.label" })}
                ?disabled=${!!this.instance}
                help=${this.instance
                    ? msg(
                          "The RP ID cannot be changed after creation, as all credentials registered for it would be invalidated.",
                          { id: "webauthn-rp-config.form.rp-id.description.immutable" },
                      )
                    : msg(
                          "WebAuthn Relying Party ID that credentials are bound to, e.g. sso.example.com. Cannot be changed after creation.",
                          { id: "webauthn-rp-config.form.rp-id.description" },
                      )}
            ></ak-text-input>

            <ak-textarea-input
                required
                name="origins"
                input-hint="code"
                value="${(this.instance?.origins ?? []).join("\n")}"
                label=${msg("Allowed origins", { id: "webauthn-rp-config.form.origins.label" })}
                help=${msg(
                    "One origin per line. Origins allowed to perform WebAuthn ceremonies for this RP ID: exact https:// origins (e.g. https://sso.example.com) or android:apk-key-hash: origins for native apps. Every listed origin can run full WebAuthn ceremonies for this RP ID; only list origins you control.",
                    { id: "webauthn-rp-config.form.origins.description" },
                )}
            ></ak-textarea-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-webauthn-rp-config-form": WebAuthnRPConfigForm;
    }
}
