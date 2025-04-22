import { css } from "lit";

// The `host` information for the Patternfly dual list selector came with some default settings that
// we do not want in a web component. By isolating what we *really* use into this collection here,
// we get all the benefits of Patternfly without having to wrestle without also having to counteract
// those default settings.

export const globalVariables = css`
    :host {
        --pf-c-text-input-group--BackgroundColor: var(--pf-global--BackgroundColorg--100);
        --pf-c-text-input-group--Color: var(--pf-global--Color--dark-100);

        --pf-c-text-input-group__text--before--BorderWidth: var(--pf-global--BorderWidth--sm);
        --pf-c-text-input-group__text--before--BorderColor: var(--pf-global--BorderColor--300);

        --pf-c-text-input-group__text--after--BorderBottomWidth: var(--pf-global--BorderWidth--sm);
        --pf-c-text-input-group__text--after--BorderBottomColor: var(--pf-global--BorderColor--200);

        --pf-c-text-input-group--hover__text--after--BorderBottomColor: var(
            --pf-global--primary-color--100
        );
        --pf-c-text-input-group__text--focus-within--after--BorderBottomWidth: var(
            --pf-global--BorderWidth--md
        );
        --pf-c-text-input-group__text--focus-within--after--BorderBottomColor: var(
            --pf-global--primary-color--100
        );
        --pf-c-text-input-group__main--first-child--not--text-input--MarginLeft: var(
            --pf-global--spacer--sm
        );
        --pf-c-text-input-group__main--m-icon__text-input--PaddingLeft: var(
            --pf-global--spacer--xl
        );
        --pf-c-text-input-group__main--RowGap: var(--pf-global--spacer--xs);
        --pf-c-text-input-group__main--ColumnGap: var(--pf-global--spacer--sm);
        --pf-c-text-input-group--c-chip-group__main--PaddingTop: var(--pf-global--spacer--xs);
        --pf-c-text-input-group--c-chip-group__main--PaddingRight: var(--pf-global--spacer--xs);
        --pf-c-text-input-group--c-chip-group__main--PaddingBottom: var(--pf-global--spacer--xs);
        --pf-c-text-input-group__text-input--PaddingTop: var(--pf-global--spacer--form-element);
        --pf-c-text-input-group__text-input--PaddingRight: var(--pf-global--spacer--sm);
        --pf-c-text-input-group__text-input--PaddingBottom: var(--pf-global--spacer--form-element);
        --pf-c-text-input-group__text-input--PaddingLeft: var(--pf-global--spacer--sm);
        --pf-c-text-input-group__text-input--MinWidth: 12ch;
        --pf-c-text-input-group__text-input--m-hint--Color: var(--pf-global--Color--dark-200);
        --pf-c-text-input-group--placeholder--Color: var(--pf-global--Color--dark-200);
        --pf-c-text-input-group__icon--Left: var(--pf-global--spacer--sm);
        --pf-c-text-input-group__icon--Color: var(--pf-global--Color--200);
        --pf-c-text-input-group__text--hover__icon--Color: var(--pf-global--Color--100);
        --pf-c-text-input-group__icon--TranslateY: -50%;
        --pf-c-text-input-group__utilities--MarginRight: var(--pf-global--spacer--sm);
        --pf-c-text-input-group__utilities--MarginLeft: var(--pf-global--spacer--xs);
        --pf-c-text-input-group__utilities--child--MarginLeft: var(--pf-global--spacer--xs);
        --pf-c-text-input-group__utilities--c-button--PaddingRight: var(--pf-global--spacer--xs);
        --pf-c-text-input-group__utilities--c-button--PaddingLeft: var(--pf-global--spacer--xs);
        --pf-c-text-input-group--m-disabled--Color: var(--pf-global--disabled-color--100);
        --pf-c-text-input-group--m-disabled--BackgroundColor: var(--pf-global--disabled-color--300);
    }

    @media (prefers-color-scheme: dark) {
        :host {
            --pf-c-text-input-group--BackgroundColor: var(--ak-dark-background-light);
            --pf-c-text-input-group--Color: var(--ak-dark-foreground);

            --pf-c-text-input-group__text--before--BorderColor: var(--ak-dark-background-lighter);
            --pf-c-text-input-group__text--before--BorderWidth: 0;

            --pf-c-text-input-group--m-disabled--Color: var(--pf-global--disabled-color--300);
            --pf-c-text-input-group--m-disabled--BackgroundColor: var(
                --pf-global--disabled-color--200
            );

            --pf-c-text-input-group__text--before--BorderBottomColor: var(
                --pf-global--BorderColor--200
            );
        }
    }
`;

export const searchStyles = css`
    i.fa,
    i.fas,
    i.far,
    i.fal,
    i.fab {
        -moz-osx-font-smoothing: grayscale;
        -webkit-font-smoothing: antialiased;
        display: inline-block;
        font-style: normal;
        font-variant: normal;
        text-rendering: auto;
        line-height: 1;
    }

    i.fa-search:before {
        content: "\f002";
    }

    .fa,
    .fas {
        position: relative;
        font-family: "Font Awesome 5 Free";
        font-weight: 900;
    }

    i.fa-fw {
        text-align: center;
        width: 1.25em;
    }

    .pf-c-text-input-group {
        position: relative;
        display: flex;
        width: 100%;
        color: var(--pf-c-text-input-group--Color, inherit);
        background-color: var(--pf-c-text-input-group--BackgroundColor);
    }

    .pf-c-text-input-group__main {
        display: flex;
        flex: 1;
        flex-wrap: wrap;
        gap: var(--pf-c-text-input-group__main--RowGap)
            var(--pf-c-text-input-group__main--ColumnGap);
        min-width: 0;
    }

    .pf-c-text-input-group__main.pf-m-icon {
        --pf-c-text-input-group__text-input--PaddingLeft: var(
            --pf-c-text-input-group__main--m-icon__text-input--PaddingLeft
        );
    }
    .pf-c-text-input-group__text {
        display: inline-grid;
        grid-template-columns: 1fr;
        grid-template-areas: "text-input";
        flex: 1;
        z-index: 0;
    }

    .pf-c-text-input-group__text::before {
        border-width: var(--pf-c-text-input-group__text--before--BorderWidth);
        border-color: var(--pf-c-text-input-group__text--before--BorderColor);
        border-bottom-color: var(--pf-c-text-input-group__text--after--BorderBottomColor);
        border-bottom-width: var(--pf-c-text-input-group__text--after--BorderBottomWidth);
        border-style: solid;
    }

    .pf-c-text-input-group__text::after {
        border-bottom: var(--pf-c-text-input-group__text--after--BorderBottomWidth) solid
            var(--pf-c-text-input-group__text--after--BorderBottomColor);
    }

    .pf-c-text-input-group__text::before,
    .pf-c-text-input-group__text::after {
        position: absolute;
        top: 0;
        right: 0;
        bottom: 0;
        left: 0;
        pointer-events: none;
        content: "";
        z-index: 2;
    }

    .pf-c-text-input-group__icon {
        z-index: 4;
        position: absolute;
        top: 50%;
        left: var(--pf-c-text-input-group__icon--Left);
        color: var(--pf-c-text-input-group__icon--Color);
        transform: translateY(var(--pf-c-text-input-group__icon--TranslateY));
    }

    .pf-c-text-input-group__text-input,
    .pf-c-text-input-group__text-input.pf-m-hint {
        grid-area: text-input;
    }

    .pf-c-text-input-group__text-input {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        position: relative;
        width: 100%;
        color: var(--pf-c-text-input-group--Color);
        background-color: var(--pf-c-text-input-group--BackgroundColor);
        min-width: var(--pf-c-text-input-group__text-input--MinWidth);
        padding: var(--pf-c-text-input-group__text-input--PaddingTop)
            var(--pf-c-text-input-group__text-input--PaddingRight)
            var(--pf-c-text-input-group__text-input--PaddingBottom)
            var(--pf-c-text-input-group__text-input--PaddingLeft);
        border: 0;
    }
`;
