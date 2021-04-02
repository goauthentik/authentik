import { CSSResult, customElement, html, LitElement, TemplateResult } from "lit-element";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import AKGlobal from "../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import "../elements/forms/FormGroup";

@customElement("ak-test-page")
export class TestPage extends LitElement {

    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFButton, PFFormControl, AKGlobal];
    }

    render(): TemplateResult {
        return html`<form novalidate class="pf-c-form">
            <div class="pf-c-form__group">
                <div class="pf-c-form__group-label">
                    <label class="pf-c-form__label" for="form-expandable-field-groups-label1">
                        <span class="pf-c-form__label-text">Label 1</span>
                        <span class="pf-c-form__label-required" aria-hidden="true">&#42;</span>
                    </label>
                    <button class="pf-c-form__group-label-help" aria-label="More info">
                        <i class="pficon pf-icon-help" aria-hidden="true"></i>
                    </button>
                </div>
                <div class="pf-c-form__group-control">
                    <input class="pf-c-form-control" type="text" id="form-expandable-field-groups-label1"
                        name="form-expandable-field-groups-label1" required />
                </div>
            </div>
            <div class="pf-c-form__group">
                <div class="pf-c-form__group-label">
                    <label class="pf-c-form__label" for="form-expandable-field-groups-label2">
                        <span class="pf-c-form__label-text">Label 2</span>
                        <span class="pf-c-form__label-required" aria-hidden="true">&#42;</span>
                    </label>
                    <button class="pf-c-form__group-label-help" aria-label="More info">
                        <i class="pficon pf-icon-help" aria-hidden="true"></i>
                    </button>
                </div>
                <div class="pf-c-form__group-control">
                    <input class="pf-c-form-control" type="text" id="form-expandable-field-groups-label2"
                        name="form-expandable-field-groups-label2" required />
                </div>
            </div>
            <ak-form-group>
                <span slot="header">
                    foo
                </span>
                <div slot="body">
                    <div class="pf-c-form__group">
                        <div class="pf-c-form__group-label">
                            <label class="pf-c-form__label" for="form-expandable-field-groups-field-group2-label1">
                                <span class="pf-c-form__label-text">Label 1</span>
                                <span class="pf-c-form__label-required" aria-hidden="true">*</span>
                            </label>
                            <button class="pf-c-form__group-label-help" aria-label="More info">
                                <i class="pficon pf-icon-help" aria-hidden="true"></i>
                            </button>
                        </div>
                        <div class="pf-c-form__group-control">
                            <input class="pf-c-form-control" type="text" id="form-expandable-field-groups-field-group2-label1" name="form-expandable-field-groups-field-group2-label1" required="">
                        </div>
                    </div>
                    <div class="pf-c-form__group">
                        <div class="pf-c-form__group-label">
                            <label class="pf-c-form__label" for="form-expandable-field-groups-field-group2-label2">
                                <span class="pf-c-form__label-text">Label 2</span>
                                <span class="pf-c-form__label-required" aria-hidden="true">*</span>
                            </label>
                            <button class="pf-c-form__group-label-help" aria-label="More info">
                                <i class="pficon pf-icon-help" aria-hidden="true"></i>
                            </button>
                        </div>
                        <div class="pf-c-form__group-control">
                            <input class="pf-c-form-control" type="text" id="form-expandable-field-groups-field-group2-label2" name="form-expandable-field-groups-field-group2-label2" required="">
                        </div>
                    </div>
                </div>
            </ak-form-group>
        </form>`;
    }

}
