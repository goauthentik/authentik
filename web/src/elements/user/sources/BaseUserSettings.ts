import { AKElement } from "@goauthentik/elements/Base";

import { CSSResult } from "lit";
import { property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export abstract class BaseUserSettings extends AKElement {
    @property()
    objectId!: string;

    @property()
    configureUrl?: string;

    static get styles(): CSSResult[] {
        return [PFBase, PFButton, PFForm, PFFormControl];
    }
}
