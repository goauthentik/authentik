import { css } from "lit";

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
    }
`;

export const mainStyles = css`
    .pf-c-dual-list-selector__title-text {
        font-weight: var(--pf-c-dual-list-selector__title-text--FontWeight);
    }

    .pf-c-dual-list-selector__status-text {
        font-size: var(--pf-c-dual-list-selector__status-text--FontSize);
        color: var(--pf-c-dual-list-selector__status-text--Color);
    }

    .ak-dual-list-selector {
        display: grid;
        grid-template-columns:
            minmax(
                var(--pf-c-dual-list-selector--GridTemplateColumns--pane--MinMax--min),
                var(--pf-c-dual-list-selector--GridTemplateColumns--pane--MinMax--max)
            )
            min-content
            minmax(
                var(--pf-c-dual-list-selector--GridTemplateColumns--pane--MinMax--min),
                var(--pf-c-dual-list-selector--GridTemplateColumns--pane--MinMax--max)
            );
    }
`;

export const selectedPaneStyles = css`
.pf-c-dual-list-selector__menu {
height: 100%;
}
.pf-c-dual-list-selector__item {
padding: 0.25rem;
}
input[type="checkbox"][readonly] {
pointer-events: none;
}
`;
