import { css, CSSResult } from "lit-element";
// @ts-ignore
import PF from "@patternfly/patternfly/patternfly.css";
// @ts-ignore
import PFAddons from "@patternfly/patternfly/patternfly-addons.css";
// @ts-ignore
import FA from "@fortawesome/fontawesome-free/css/fontawesome.css";
// @ts-ignore
import AKGlobal from "../authentik.css";
// @ts-ignore
import CodeMirrorStyle from "codemirror/lib/codemirror.css";
// @ts-ignore
import CodeMirrorTheme from "codemirror/theme/monokai.css";
export const ColorStyles = css`
    .pf-m-success {
        color: var(--pf-global--success-color--100);
    }
    .pf-c-button.pf-m-success {
        color: var(--pf-c-button--m-primary--Color);
        background-color: var(--pf-global--success-color--100);
    }
    .pf-m-warning {
        color: var(--pf-global--warning-color--100);
    }
    .pf-c-button.pf-m-warning {
        color: var(--pf-c-button--m-primary--Color);
        background-color: var(--pf-global--warning-color--100);
    }
    .pf-m-danger {
        color: var(--pf-global--danger-color--100);
    }
    .pf-c-button.pf-m-danger {
        color: var(--pf-c-button--m-primary--Color);
        background-color: var(--pf-global--danger-color--100);
    }
`;
export const COMMON_STYLES: CSSResult[] = [PF, PFAddons, FA, AKGlobal, CodeMirrorStyle, CodeMirrorTheme, ColorStyles];
