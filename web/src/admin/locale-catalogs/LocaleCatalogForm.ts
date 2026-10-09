import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";
import "#components/ak-switch-input";
import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";

import { AdminApi, LocaleCatalog, LocaleCatalogRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-locale-catalog-form")
export class LocaleCatalogForm extends ModelForm<LocaleCatalog, string> {
    protected endpoints = {
        load: (catalogUuid: string) =>
            aki(AdminApi).adminLocaleCatalogsRetrieve({
                catalogUuid,
            }),
        create: (localeCatalogRequest: LocaleCatalogRequest) =>
            aki(AdminApi).adminLocaleCatalogsCreate({
                localeCatalogRequest,
            }),
        update: (catalogUuid: string, localeCatalogRequest: LocaleCatalogRequest) =>
            aki(AdminApi).adminLocaleCatalogsUpdate({
                catalogUuid,
                localeCatalogRequest,
            }),
    };

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated locale catalog.", {
                  id: "locale-catalog.form.update.success",
              })
            : msg("Successfully created locale catalog.", {
                  id: "locale-catalog.form.create.success",
              });
    }

    protected override renderForm(): TemplateResult {
        return html`<ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Locale", { id: "locale-catalog.form.locale.label" })}
                required
                name="locale"
            >
                <input
                    type="text"
                    value="${ifDefined(this.instance?.locale)}"
                    class="pf-c-form-control"
                    placeholder="de-DE"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Language tag such as de or de-DE. Catalogs for a language without a region apply to all of its regions.",
                        { id: "locale-catalog.form.locale.description" },
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-switch-input
                name="enabled"
                label=${msg("Enabled")}
                ?checked=${this.instance?.enabled ?? true}
            >
            </ak-switch-input>
            <ak-form-element-horizontal label=${msg("Order")} required name="order">
                <input
                    type="number"
                    value="${this.instance?.order ?? 0}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "When multiple catalogs for the same locale translate the same message, the catalog with the highest order wins.",
                        { id: "locale-catalog.form.order.description" },
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Messages", { id: "locale-catalog.form.messages.label" })}
                name="messages"
            >
                <ak-codemirror .value=${this.instance?.messages ?? {}}></ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "YAML or JSON object mapping English source strings, or message IDs, to their translation. Use ${0}, ${1}, ... for placeholders in the web interface and %(name)s in server-rendered messages.",
                        { id: "locale-catalog.form.messages.description" },
                    )}
                </p>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-locale-catalog-form": LocaleCatalogForm;
    }
}
