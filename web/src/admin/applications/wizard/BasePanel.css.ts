import { css } from "lit";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFSwitch from "@patternfly/patternfly/components/Switch/switch.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export const styles = [
    PFBase,
    PFCard,
    PFButton,
    PFForm,
    PFAlert,
    PFRadio,
    PFInputGroup,
    PFFormControl,
    PFSwitch,
    css`
        select[multiple] {
            height: 15em;
        }
    `,
];
