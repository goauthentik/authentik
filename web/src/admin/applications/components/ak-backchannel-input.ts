import "#admin/applications/ak-provider-table";
import "#elements/forms/HorizontalFormElement";
import "#elements/chips/Chip";
import "#elements/chips/ChipGroup";
import "#elements/forms/Form";

import { AKElement } from "#elements/Base";
import { renderModal } from "#elements/dialogs";
import { AKFormSubmitEvent } from "#elements/forms/Form";
import { SlottedTemplateResult } from "#elements/types";

import { Provider } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { map } from "lit/directives/map.js";

@customElement("ak-backchannel-providers-input")
export class AkBackchannelProvidersInput extends AKElement {
    // Render into the lightDOM. This effectively erases the shadowDOM nature of this component, but
    // we're not actually using that and, for the meantime, we need the form handlers to be able to
    // find the children of this component.
    //
    // This field is so highly specialized that it would make more sense if we put the API and the
    // fetcher here.
    //
    // TODO: This abstraction is wrong; it's putting *more* layers in as a way of managing the
    // visual clutter and legibility issues of ak-form-elemental-horizontal and patternfly in
    // general.

    protected createRenderRoot() {
        return this as HTMLElement;
    }

    @property({ type: String })
    public name!: string;

    @property({ type: String })
    public label = "";

    @property({ type: Array })
    public providers: Provider[] = [];

    @property({ attribute: false, type: Object })
    public tooltip?: SlottedTemplateResult;

    @property({ attribute: false, type: Object })
    public confirm!: (items: Provider[]) => Promise<void>;

    @property({ attribute: false, type: Object })
    public remover!: (provider: Provider) => () => void;

    @property({ type: String })
    public value = "";

    @property({ type: Boolean })
    public required = false;

    @property({ type: String })
    public help = "";

    protected openSelectBackchannelProvidersModal = () => {
        return renderModal(html`
            <ak-form
                headline=${this.label}
                submit-label=${msg("Confirm")}
                @submit=${(event: AKFormSubmitEvent<Provider[]>) => {
                    const providers = event.target.toJSON();

                    this.confirm(providers);
                }}
            >
                ${this.help ? html`<p class="pf-c-form__helper-text">${this.help}</p>` : nothing}
                <ak-provider-table backchannel></ak-provider-table>
            </ak-form>
        `);
    };

    render() {
        const renderOneChip = (provider: Provider) =>
            html`<ak-chip
                removable
                value=${ifDefined(provider.pk)}
                @remove=${this.remover(provider)}
                >${provider.name}</ak-chip
            >`;

        return html`
            <ak-form-element-horizontal label=${this.label} name=${this.name}>
                <div class="pf-c-input-group">
                    <button
                        class="pf-c-button pf-m-control"
                        type="button"
                        @click=${this.openSelectBackchannelProvidersModal}
                    >
                        ${this.tooltip ? this.tooltip : nothing}
                        <i class="fas fa-plus" aria-hidden="true"></i>
                    </button>
                    <div class="pf-c-form-control">
                        <ak-chip-group
                            @click=${this.openSelectBackchannelProvidersModal}
                            placeholder=${msg("Select one or more backchannel providers...")}
                            >${map(this.providers, renderOneChip)}</ak-chip-group
                        >
                    </div>
                </div>
                ${this.help ? html`<p class="pf-c-form__helper-text">${this.help}</p>` : nothing}
            </ak-form-element-horizontal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-backchannel-providers-input": AkBackchannelProvidersInput;
    }
}
