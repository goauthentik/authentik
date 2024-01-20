import { css } from "lit";

import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export const sidebarItemStyles = [
    PFBase,
    PFPage,
    PFNav,
    css`
        :host {
            z-index: 100;
            box-shadow: none !important;
        }

        .highlighted {
            background-color: var(--ak-accent);
            margin: 16px;
        }

        .highlighted .pf-c-nav__link {
            padding-left: 0.5rem;
        }

        .pf-c-nav__link.pf-m-current::after,
        .pf-c-nav__link.pf-m-current:hover::after,
        .pf-c-nav__item.pf-m-current:not(.pf-m-expanded) .pf-c-nav__link::after {
            --pf-c-nav__link--m-current--after--BorderColor: #fd4b2d;
        }

        .pf-c-nav__item .pf-c-nav__item::before {
            border-bottom-width: 0;
        }

        .pf-c-nav__section + .pf-c-nav__section {
            --pf-c-nav__section--section--MarginTop: var(--pf-global--spacer--sm);
        }
        .pf-c-nav__list .sidebar-brand {
            max-height: 82px;
            margin-bottom: -0.5rem;
        }
        .pf-c-nav__toggle {
            width: calc(var(--pf-c-nav__toggle--FontSize) + calc(2 * var(--pf-global--spacer--md)));
        }

        nav {
            display: flex;
            flex-direction: column;
            max-height: 100vh;
            height: 100%;
            overflow-y: hidden;
        }
        .pf-c-nav__list {
            flex: 1 0 1fr;
            overflow-y: auto;
        }

        .pf-c-nav__link {
            --pf-c-nav__link--PaddingTop: 0.5rem;
            --pf-c-nav__link--PaddingRight: 0.5rem;
            --pf-c-nav__link--PaddingBottom: 0.5rem;
        }

        .pf-c-nav__link a {
            flex: 1 0 max-content;
            color: var(--pf-c-nav__link--Color);
        }

        a.pf-c-nav__link:hover {
            color: var(--pf-c-nav__link--Color);
            text-decoration: var(--pf-global--link--TextDecoration--hover);
        }

        .pf-c-nav__section-title {
            font-size: 12px;
        }
        .pf-c-nav__item {
            --pf-c-nav__item--MarginTop: 0px;
        }

        .pf-c-nav__toggle-icon {
            padding: var(--pf-global--spacer--sm) var(--pf-global--spacer--md);
        }
    `,
];
