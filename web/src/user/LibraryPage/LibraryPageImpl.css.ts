import { css } from "lit";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";

export const styles = [PFBase, PFDisplay, PFEmptyState, PFPage, PFContent].concat(css`
    :host {
        display: block;
        padding: 3% 5%;
    }
    .header {
        display: flex;
        flex-direction: row;
        justify-content: space-between;
    }
    .header input {
        width: 30ch;
        box-sizing: border-box;
        border: 0;
        border-bottom: 1px solid;
        border-bottom-color: #fd4b2d;
        background-color: transparent;
        font-size: 1.5rem;
    }
    .header input:focus {
        outline: 0;
    }
    .pf-c-page__main {
        overflow: hidden;
    }
    .pf-c-page__main-section {
        background-color: transparent;
    }
`);

export default styles;
