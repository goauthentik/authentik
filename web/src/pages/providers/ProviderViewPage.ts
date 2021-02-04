import { gettext } from "django";
import { customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { Provider } from "../../api/Providers";
import { PBResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import { TableColumn } from "../../elements/table/Table";

@customElement("ak-provider-view")
export class ProviderViewPage extends LitElement {
    @property()
    set args(value: { [key: string]: number }) {
        this.providerID = value.id;
    }

    @property()
    set providerID(value: number) {
        Provider.get(value).then((app) => (this.provider = app));
    }

    @property({ attribute: false })
    provider?: Provider;

}
