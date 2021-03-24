import { CSSResult, LitElement, property } from "lit-element";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import AKGlobal from "../../../authentik.css";

export abstract class BaseUserSettings extends LitElement {

    @property()
    objectId!: string;

    static get styles(): CSSResult[] {
        return [PFBase, PFCard, PFButton, AKGlobal];
    }
}

