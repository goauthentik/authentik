import "#elements/forms/HorizontalFormElement";
import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import { SearchSelectSource, withQuery } from "#elements/forms/SearchSelect/shared";
import { SlottedTemplateResult } from "#elements/types";

import { AKLabel } from "#components/ak-label";
import { AKSearchSelect } from "#components/ak-search-select-field";

import {
    AdminApi,
    BrandLocaleCatalog,
    BrandLocaleCatalogRequest,
    LocaleCatalog,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

const catalogSource: SearchSelectSource<LocaleCatalog> = {
    fetchObjects: (query) =>
        aki(AdminApi)
            .adminLocaleCatalogsList(withQuery(query, { ordering: "name" }))
            .then(({ results }) => results),
    keyOf: (catalog) => catalog.catalogUuid,
    labelOf: (catalog) =>
        msg(str`${catalog.name} (${catalog.locale})`, {
            id: "locale-catalog.binding.form.catalog.option",
        }),
};

@customElement("ak-brand-locale-catalog-form")
export class BrandLocaleCatalogForm extends ModelForm<BrandLocaleCatalog, string> {
    public static override verboseName = msg("Locale Catalog Binding", {
        id: "locale-catalog.binding.verbose-name",
    });
    public static override verboseNamePlural = msg("Locale Catalog Bindings", {
        id: "locale-catalog.binding.verbose-name-plural",
    });

    /**
     * The brand new bindings are created for.
     */
    @property({ attribute: false })
    public brandPk?: string;

    protected endpoints = {
        load: (bindingUuid: string) =>
            aki(AdminApi).adminLocaleCatalogBindingsRetrieve({ bindingUuid }),
        create: (data: BrandLocaleCatalogRequest) =>
            aki(AdminApi).adminLocaleCatalogBindingsCreate({
                brandLocaleCatalogRequest: { ...data, brand: this.brandPk ?? data.brand },
            }),
        update: (bindingUuid: string, data: BrandLocaleCatalogRequest) =>
            aki(AdminApi).adminLocaleCatalogBindingsPartialUpdate({
                bindingUuid,
                patchedBrandLocaleCatalogRequest: data,
            }),
    };

    protected override renderForm(): SlottedTemplateResult {
        return html`<ak-form-element-horizontal required name="catalog">
                ${AKLabel(
                    { slot: "label", className: "pf-c-form__group-label", required: true },
                    msg("Locale Catalog", { id: "locale-catalog.binding.form.catalog.label" }),
                )}
                ${AKSearchSelect({
                    name: "catalog",
                    source: catalogSource,
                    label: msg("Locale Catalog", {
                        id: "locale-catalog.binding.form.catalog.label",
                    }),
                    placeholder: msg("Select a locale catalog...", {
                        id: "locale-catalog.binding.form.catalog.placeholder",
                    }),
                    value: this.instance?.catalog,
                    selectedObject: this.instance?.catalogObj,
                    blankable: false,
                })}
            </ak-form-element-horizontal>
            <ak-form-element-horizontal required name="order">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "locale-catalog-binding-order",
                        required: true,
                    },
                    msg("Order"),
                )}
                <input
                    id="locale-catalog-binding-order"
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
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-brand-locale-catalog-form": BrandLocaleCatalogForm;
    }
}
