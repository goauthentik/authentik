import { CSSResult, LitElement, property } from "lit-element";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import AKGlobal from "../../../authentik.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";

export abstract class BaseUserSettings extends LitElement {

    @property()
    objectId!: string;

    static get styles(): CSSResult[] {
        return [PFBase, PFCard, PFButton, PFForm, PFFormControl, AKGlobal];
    }
}

