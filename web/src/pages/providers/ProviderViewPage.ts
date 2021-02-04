import { customElement, LitElement, property } from "lit-element";
import { Provider } from "../../api/Providers";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";

@customElement("ak-provider-view")
export class ProviderViewPage extends LitElement {
    @property()
    set args(value: { [key: string]: number }) {
        this.providerID = value.id;
    }

    @property({type: Number})
    set providerID(value: number) {
        Provider.get(value).then((app) => (this.provider = app));
    }

    @property({ attribute: false })
    provider?: Provider;

}
