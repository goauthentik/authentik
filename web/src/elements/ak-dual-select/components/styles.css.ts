import { css } from "lit";

// The `host` information for the Patternfly dual list selector came with some default settings that
// we do not want in a web component. By isolating what we *really* use into this collection here,
// we get all the benefits of Patternfly without having to wrestle without also having to counteract
// those default settings.

export const globalVariables = css`
    :host {
        --pf-c-dual-list-selector--GridTemplateColumns--pane--MinMax--min: 12.5rem;
        --pf-c-dual-list-selector--GridTemplateColumns--pane--MinMax--max: 28.125rem;
        --pf-c-dual-list-selector__header--MarginBottom: var(--pf-global--spacer--sm);
        --pf-c-dual-list-selector__title-text--FontWeight: var(--pf-global--FontWeight--bold);
        --pf-c-dual-list-selector__tools--MarginBottom: var(--pf-global--spacer--md);
        --pf-c-dual-list-selector__tools-filter--tools-actions--MarginLeft: var(
            --pf-global--spacer--sm
        );
        --pf-c-dual-list-selector__menu--BorderWidth: var(--pf-global--BorderWidth--sm);
        --pf-c-dual-list-selector__menu--BorderColor: var(--pf-global--BorderColor--100);
        --pf-c-dual-list-selector__menu--MinHeight: 12.5rem;
        --pf-c-dual-list-selector__menu--MaxHeight: 20rem;
        --pf-c-dual-list-selector__list-item-row--FontSize: var(--pf-global--FontSize--sm);
        --pf-c-dual-list-selector__list-item-row--BackgroundColor: transparent;
        --pf-c-dual-list-selector__list-item-row--hover--BackgroundColor: var(
            --pf-global--BackgroundColor--light-300
        );
        --pf-c-dual-list-selector__list-item-row--focus-within--BackgroundColor: var(
            --pf-global--BackgroundColor--light-300
        );
        --pf-c-dual-list-selector__list-item-row--m-selected--BackgroundColor: var(
            --pf-global--BackgroundColor--light-300
        );
        --pf-c-dual-list-selector__list-item--m-ghost-row--BackgroundColor: var(
            --pf-global--BackgroundColor--100
        );
        --pf-c-dual-list-selector__list-item--m-ghost-row--Opacity: 0.4;
        --pf-c-dual-list-selector__item--PaddingTop: var(--pf-global--spacer--sm);
        --pf-c-dual-list-selector__item--PaddingRight: var(--pf-global--spacer--md);
        --pf-c-dual-list-selector__item--PaddingBottom: var(--pf-global--spacer--sm);
        --pf-c-dual-list-selector__item--PaddingLeft: var(--pf-global--spacer--md);
        --pf-c-dual-list-selector__item--m-expandable--PaddingLeft: 0;
        --pf-c-dual-list-selector__item--indent--base: calc(
            var(--pf-global--spacer--md) + var(--pf-global--spacer--sm) +
                var(--pf-c-dual-list-selector__list-item-row--FontSize)
        );
        --pf-c-dual-list-selector__item--nested-indent--base: calc(
            var(--pf-c-dual-list-selector__item--indent--base) - var(--pf-global--spacer--md)
        );
        --pf-c-dual-list-selector__draggable--item--PaddingLeft: var(--pf-global--spacer--xs);
        --pf-c-dual-list-selector__item-text--Color: var(--pf-global--Color--100);
        --pf-c-dual-list-selector__list-item-row--m-selected__text--Color: var(
            --pf-global--active-color--100
        );
        --pf-c-dual-list-selector__list-item-row--m-selected__text--FontWeight: var(
            --pf-global--FontWeight--bold
        );
        --pf-c-dual-list-selector__list-item--m-disabled__item-text--Color: var(
            --pf-global--disabled-color--100
        );
        --pf-c-dual-list-selector__status--MarginBottom: var(--pf-global--spacer--sm);
        --pf-c-dual-list-selector__status-text--FontSize: var(--pf-global--FontSize--sm);
        --pf-c-dual-list-selector__status-text--Color: var(--pf-global--Color--200);
        --pf-c-dual-list-selector__controls--PaddingRight: var(--pf-global--spacer--md);
        --pf-c-dual-list-selector__controls--PaddingLeft: var(--pf-global--spacer--md);
        --pf-c-dual-list-selector__item-toggle--PaddingTop: var(--pf-global--spacer--sm);
        --pf-c-dual-list-selector__item-toggle--PaddingRight: var(--pf-global--spacer--sm);
        --pf-c-dual-list-selector__item-toggle--PaddingBottom: var(--pf-global--spacer--sm);
        --pf-c-dual-list-selector__item-toggle--PaddingLeft: var(--pf-global--spacer--md);
        --pf-c-dual-list-selector__item-toggle--MarginTop: calc(var(--pf-global--spacer--sm) * -1);
        --pf-c-dual-list-selector__item-toggle--MarginBottom: calc(
            var(--pf-global--spacer--sm) * -1
        );
        --pf-c-dual-list-selector__list__list__item-toggle--Left: 0;
        --pf-c-dual-list-selector__list__list__item-toggle--TranslateX: -100%;
        --pf-c-dual-list-selector__item-check--MarginRight: var(--pf-global--spacer--sm);
        --pf-c-dual-list-selector__item-count--Marginleft: var(--pf-global--spacer--sm);
        --pf-c-dual-list-selector__item--c-badge--m-read--BackgroundColor: var(
            --pf-global--disabled-color--200
        );
        --pf-c-dual-list-selector__item-toggle-icon--Rotate: 0;
        --pf-c-dual-list-selector__list-item--m-expanded__item-toggle-icon--Rotate: 90deg;
        --pf-c-dual-list-selector__item-toggle-icon--Transition: var(--pf-global--Transition);
        --pf-c-dual-list-selector__item-toggle-icon--MinWidth: var(
            --pf-c-dual-list-selector__list-item-row--FontSize
        );
        --pf-c-dual-list-selector__list-item--m-disabled__item-toggle-icon--Color: var(
            --pf-global--disabled-color--200
        );

        /* Unique to authentik */
        --pf-c-dual-list-selector--selection-desc--FontSize: var(--pf-global--FontSize--xs);
        --pf-c-dual-list-selector--selection-desc--Color: var(--pf-global--Color--dark-200);
        --pf-c-dual-list-selector__status--top-padding: var(--pf-global--spacer--xs);
        --pf-c-dual-list-panels__gap: var(--pf-global--spacer--xs);
    }

    @media (prefers-color-scheme: dark) {
        :host {
            --pf-c-dual-list-selector__menu--BorderColor: var(--ak-dark-background-lighter);
            --pf-c-dual-list-selector__item-text--Color: var(--ak-dark-foreground);
            --pf-c-dual-list-selector__list-item-row--BackgroundColor: var(
                --ak-dark-background-light-ish
            );
            --pf-c-dual-list-selector__list-item-row--hover--BackgroundColor: var(
                --ak-dark-background-lighter;
            );
            --pf-c-dual-list-selector__list-item-row--hover--BackgroundColor: var(
                --pf-global--BackgroundColor--400
            );
        }
    }
`;

export const mainStyles = css`
    :host {
        --pf-c-dual-list-selector--GridTemplateColumns--pane--MinMax--min: 12.5rem;
        --pf-c-dual-list-selector--GridTemplateColumns--pane--MinMax--max: 28.125rem;
    }
    :host {
        display: block grid;
    }

    .pf-c-dual-list-selector__title-text {
        font-weight: var(--pf-c-dual-list-selector__title-text--FontWeight);
    }

    .pf-c-dual-list-selector__status {
        padding-top: var(--pf-c-dual-list-selector__status--top-padding);
    }

    .pf-c-dual-list-selector__status-text {
        font-size: var(--pf-c-dual-list-selector__status-text--FontSize);
        color: var(--pf-c-dual-list-selector__status-text--Color);
    }

    .ak-dual-list-selector {
        display: grid;
        grid-template-columns: minmax(0, 1fr) min-content minmax(0, 1fr);
    }

    .ak-available-pane,
    .ak-selected-pane {
        display: grid;
        grid-template-rows: auto auto auto 1fr auto;
        gap: var(--pf-c-dual-list-panels__gap);
        max-width: 100%;
        overflow: hidden;
    }

    ak-dual-select-controls {
        height: 100%;
    }
`;

export const listStyles = css`
    :host {
        display: block;
        overflow: hidden;
        max-width: 100%;
    }

    .pf-c-dual-list-selector__menu {
        max-width: 100%;
        height: 100%;
    }

    .pf-c-dual-list-selector__list {
        max-width: 100%;
        display: block;
    }

    .pf-c-dual-list-selector__item {
        padding: 0.25rem;
        width: auto;
    }

    .pf-c-dual-list-selector__item-text {
        user-select: none;
        flex-grow: 0;
    }

    .pf-c-dual-list-selector__item-text .selection-main {
        color: var(--pf-c-dual-list-selector__item-text--Color);
    }

    .pf-c-dual-list-selector__item-text .selection-main:hover {
        color: var(--pf-c-dual-list-selector__item-text--Color);
    }

    .pf-c-dual-list-selector__item-text .selection-desc {
        font-size: var(--pf-c-dual-list-selector--selection-desc--FontSize);
        color: var(--pf-c-dual-list-selector--selection-desc--Color);
    }
`;

export const selectedPaneStyles = css`
    input[type="checkbox"][readonly] {
        pointer-events: none;
    }
`;

export const availablePaneStyles = css`
    .pf-c-dual-list-selector__item-text {
        display: grid;
        grid-template-columns: 1fr auto;
    }

    .pf-c-dual-list-selector__item-text .pf-c-dual-list-selector__item-text-selected-indicator {
        display: grid;
        justify-content: center;
        align-content: center;
    }

    .pf-c-dual-list-selector__item-text i {
        display: inline-block;
        padding-left: 1rem;
        font-weight: 200;
        color: var(--pf-c-dual-list-selector--selection-desc--Color);
        font-size: var(--pf-global--FontSize--xs);
    }
`;
