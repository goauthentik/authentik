import "@goauthentik/admin/applications/ProviderSelectModal";
import { AKElement } from "@goauthentik/elements/Base";

import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { map } from "lit/directives/map.js";

import { Provider } from "@goauthentik/api";

type AkBackchannelProvidersArgs = {
    // The name of the field, snake-to-camel'd if necessary.
    name: string;
    // The label of the field.
    label: string;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    value?: any;
    // The help message, shown at the bottom.
    help?: string;

    providers: Provider[];
    confirm: ({ items }: { items: Provider[] }) => Promise<void>;
    remove: (provider: Provider) => () => void;
};

const akBackchannelProvidersDefaults = {
    required: false,
};

export function akBackchannelProvidersInput(args: AkBackchannelProvidersArgs) {
    const { name, label, help, providers, confirm, remove } = {
        ...akBackchannelProvidersDefaults,
        ...args,
    };

    const renderOneChip = (provider: Provider) =>
        html`<ak-chip .removable=${true} value=${ifDefined(provider.pk)} @remove=${remove(provider)}
            >${provider.name}</ak-chip
        >`;

    return html`
        <ak-form-element-horizontal label=${label} name=${name}>
            <div class="pf-c-input-group">
                <ak-provider-select-table ?backchannelOnly=${true} .confirm=${confirm}>
                    <button slot="trigger" class="pf-c-button pf-m-control" type="button">
                        <i class="fas fa-plus" aria-hidden="true"></i>
                    </button>
                </ak-provider-select-table>
                <div class="pf-c-form-control">
                    <ak-chip-group> ${map(providers, renderOneChip)} </ak-chip-group>
                </div>
            </div>
            ${help ? html`<p class="pf-c-form__helper-radio">${help}</p>` : nothing}
        </ak-form-element-horizontal>
    `;
}

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
        return this;
    }

    @property({ type: String })
    name!: string;

    @property({ type: String })
    label = "";

    @property({ type: Array })
    providers: Provider[] = [];

    @property({ attribute: false, type: Object })
    confirm!: ({ items }: { items: Provider[] }) => Promise<void>;

    @property({ attribute: false, type: Object })
    remover!: (provider: Provider) => () => void;

    @property({ type: String })
    value = "";

    @property({ type: Boolean })
    required = false;

    @property({ type: String })
    help = "";

    render() {
        return akBackchannelProvidersInput({
            name: this.name,
            label: this.label,
            help: this.help.trim() !== "" ? this.help : undefined,
            providers: this.providers,
            confirm: this.confirm,
            remove: this.remover,
        });
    }
}
