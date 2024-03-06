import { css } from "lit";

export const customCSS = css`
    :host {
        --pf-c-login__main-body--PaddingBottom: var(--pf-global--spacer--2xl);
    }
    .pf-c-background-image::before {
        --pf-c-background-image--BackgroundImage: var(--ak-flow-background);
        --pf-c-background-image--BackgroundImage-2x: var(--ak-flow-background);
        --pf-c-background-image--BackgroundImage--sm: var(--ak-flow-background);
        --pf-c-background-image--BackgroundImage--sm-2x: var(--ak-flow-background);
        --pf-c-background-image--BackgroundImage--lg: var(--ak-flow-background);
    }
    .ak-hidden {
        display: none;
    }
    :host {
        position: relative;
    }
    .pf-c-drawer__content {
        background-color: transparent;
    }
    /* layouts */
    @media (min-height: 60rem) {
        .pf-c-login.stacked .pf-c-login__main {
            margin-top: 13rem;
        }
    }
    .pf-c-login__container.content-right {
        grid-template-areas:
            "header main"
            "footer main"
            ". main";
    }
    .pf-c-login.sidebar_left {
        justify-content: flex-start;
        padding-top: 0;
        padding-bottom: 0;
    }
    .pf-c-login.sidebar_left .ak-login-container,
    .pf-c-login.sidebar_right .ak-login-container {
        height: 100vh;
        background-color: var(--pf-c-login__main--BackgroundColor);
        padding-left: var(--pf-global--spacer--lg);
        padding-right: var(--pf-global--spacer--lg);
    }
    .pf-c-login.sidebar_left .pf-c-list,
    .pf-c-login.sidebar_right .pf-c-list {
        color: #000;
    }
    .pf-c-login.sidebar_right {
        justify-content: flex-end;
        padding-top: 0;
        padding-bottom: 0;
    }
    :host([theme="dark"]) .pf-c-login.sidebar_left .ak-login-container,
    :host([theme="dark"]) .pf-c-login.sidebar_right .ak-login-container {
        background-color: var(--ak-dark-background);
    }
    :host([theme="dark"]) .pf-c-login.sidebar_left .pf-c-list,
    :host([theme="dark"]) .pf-c-login.sidebar_right .pf-c-list {
        color: var(--ak-dark-foreground);
    }
    .pf-c-brand {
        padding-top: calc(
            var(--pf-c-login__main-footer-links--PaddingTop) +
                var(--pf-c-login__main-footer-links--PaddingBottom) +
                var(--pf-c-login__main-body--PaddingBottom)
        );
        max-height: 9rem;
    }
    .ak-brand {
        display: flex;
        justify-content: center;
    }
    .ak-brand img {
        padding: 0 2rem;
        max-height: inherit;
    }
`;
