import { CSSResult, LitElement } from "lit";
import { property } from "lit/decorators.js";

import AKGlobal from "@goauthentik/web/authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export abstract class BaseUserSettings extends LitElement {
    @property()
    objectId!: string;

    @property()
    configureUrl?: string;

    static get styles(): CSSResult[] {
        return [PFBase, PFButton, PFForm, PFFormControl, AKGlobal];
    }
}
