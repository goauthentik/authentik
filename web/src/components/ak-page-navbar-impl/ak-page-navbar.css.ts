import { css } from "lit";

import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFNotificationBadge from "@patternfly/patternfly/components/NotificationBadge/notification-badge.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

const AKNavbarCustomCSS = css`
    :host {
        position: sticky;
        top: 0;
        z-index: var(--pf-global--ZIndex--lg);
        --pf-c-page__header-tools--MarginRight: 0;
        --ak-brand-logo-height: var(--pf-global--FontSize--4xl, 2.25rem);
        --ak-brand-background-color: var(--pf-c-page__sidebar--m-light--BackgroundColor);
        --host-navbar-height: var(--ak-c-page-header--height, 7.5rem);
    }

    :host([theme="dark"]) {
        --ak-brand-background-color: var(--pf-c-page__sidebar--BackgroundColor);
        --pf-c-page__sidebar--BackgroundColor: var(--ak-dark-background-light);
        color: var(--ak-dark-foreground);
    }

    .main-content {
        border-bottom: var(--pf-global--BorderWidth--sm);
        border-bottom-style: solid;
        border-bottom-color: var(--pf-global--BorderColor--100);
        background-color: var(--pf-c-page--BackgroundColor);

        display: flex;
        flex-direction: row;

        display: grid;
        column-gap: var(--pf-global--spacer--sm);
        grid-template-columns: [brand] auto [toggle] auto [primary] 1fr [secondary] auto;
        grid-template-rows: auto auto;
        grid-template-areas:
            "brand toggle primary secondary"
            "brand toggle description secondary";

        @media (min-width: 769px) {
            height: var(--host-navbar-height);
        }

        @media (max-width: 768px) {
            row-gap: var(--pf-global--spacer--xs);

            align-items: center;
            grid-template-areas:
                "toggle primary secondary"
                "toggle description description";
            justify-content: space-between;
            width: 100%;
        }
    }

    .items {
        display: block;

        &.primary {
            grid-column: primary;
            grid-row: primary / description;

            align-self: center;
            padding-block: var(--pf-global--spacer--md);

            @media (max-width: 768px) {
                padding-block: var(--pf-global--spacer--sm);
            }

            &.block-sibling {
                align-self: end;
            }

            @media (min-width: 426px) {
                &.block-sibling {
                    padding-block-end: 0;
                    grid-row: primary;
                }
            }

            .accent-icon {
                height: 1.2em;
                width: 1em;

                @media (max-width: 768px) {
                    display: none;
                }
            }
        }

        &.page-description {
            padding-top: 0.3em;
            grid-area: description;
            margin-block-end: var(--pf-global--spacer--md);

            display: box;
            display: -webkit-box;
            line-clamp: 2;
            -webkit-line-clamp: 2;
            box-orient: vertical;
            -webkit-box-orient: vertical;
            overflow: hidden;

            @media (max-width: 425px) {
                display: none;
            }

            @media (min-width: 769px) {
                text-wrap: balance;
            }
        }

        &.secondary {
            grid-area: secondary;
            flex: 0 0 auto;
            justify-self: end;
            padding-block: var(--pf-global--spacer--sm);
            padding-inline-end: var(--pf-global--spacer--sm);

            @media (min-width: 769px) {
                align-content: center;
                padding-block: var(--pf-global--spacer--md);
                padding-inline-end: var(--pf-global--spacer--xl);
            }
        }
    }

    .brand {
        grid-area: brand;
        background-color: var(--ak-brand-background-color);
        height: 100%;
        width: var(--pf-c-page__sidebar--Width);
        align-items: center;
        padding-inline: var(--pf-global--spacer--sm);

        display: flex;
        justify-content: center;

        &.pf-m-collapsed {
            display: none;
        }

        @media (max-width: 1199px) {
            display: none;
        }
    }

    .sidebar-trigger {
        grid-area: toggle;
        height: 100%;
    }

    .logo {
        flex: 0 0 auto;
        height: var(--ak-brand-logo-height);

        & img {
            height: 100%;
        }
    }

    .sidebar-trigger,
    .notification-trigger {
        font-size: 1.5rem;
    }

    .notification-trigger.has-notifications {
        color: var(--pf-global--active-color--100);
    }

    .pf-c-content .page-title {
        display: box;
        display: -webkit-box;
        line-clamp: 2;
        -webkit-line-clamp: 2;
        box-orient: vertical;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    h1 {
        display: flex;
        flex-direction: row;
        align-items: center !important;
    }
`;

export const styles = [
    PFBase,
    PFButton,
    PFPage,
    PFDrawer,

    PFNotificationBadge,
    PFContent,
    PFAvatar,
    PFDropdown,
    AKNavbarCustomCSS,
];

export default styles;
