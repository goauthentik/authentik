// @ts-ignore
import PF from "@patternfly/patternfly/patternfly.css";
// @ts-ignore
import PFAddons from "@patternfly/patternfly/patternfly-addons.css";
// @ts-ignore
import FA from "@fortawesome/fontawesome-free/css/fontawesome.css";
// @ts-ignore
import PBGlobal from "../passbook.css";
import { CSSResult } from "lit-element";

export const COMMON_STYLES: CSSResult[] = [PF, PFAddons, FA, PBGlobal];
