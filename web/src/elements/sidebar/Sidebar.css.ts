import { css } from "lit";

import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export const sidebarStyles = [
    PFBase,
    PFPage,
    PFNav,
    css`
        :host {
            z-index: 100;
        }
        .pf-c-nav__link.pf-m-current::after,
        .pf-c-nav__link.pf-m-current:hover::after,
        .pf-c-nav__item.pf-m-current:not(.pf-m-expanded) .pf-c-nav__link::after {
            --pf-c-nav__link--m-current--after--BorderColor: #fd4b2d;
        }
        :host([theme="light"]) {
            border-right-color: transparent !important;
        }

        .pf-c-nav__section + .pf-c-nav__section {
            --pf-c-nav__section--section--MarginTop: var(--pf-global--spacer--sm);
        }
        .pf-c-nav__list .sidebar-brand {
            max-height: 82px;
            margin-bottom: -0.5rem;
        }
        nav {
            display: flex;
            flex-direction: column;
            max-height: 100vh;
            height: 100%;
            overflow-y: hidden;
        }

        ak-sidebar-items {
            flex-grow: 1;
            overflow-y: auto;
        }

        .pf-c-nav__link {
            --pf-c-nav__link--PaddingTop: 0.5rem;
            --pf-c-nav__link--PaddingRight: 0.5rem;
            --pf-c-nav__link--PaddingBottom: 0.5rem;
        }
        .pf-c-nav__section-title {
            font-size: 12px;
        }
        .pf-c-nav__item {
            --pf-c-nav__item--MarginTop: 0px;
        }
    `,
];
