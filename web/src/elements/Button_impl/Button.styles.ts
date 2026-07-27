import { css } from "lit";

export const styles = css`
    :host {
        position: relative;
        display: inline-block;
        --ak-c-button-_FontFamily--fallback: redhattext, helvetica, arial, sans-serif;
        --ak-c-button--FontFamily: var(
            --ak-c-button--FontFamily,
            var(--ak-c-button-_FontFamily--fallback)
        );
    }

    [part="button"] {
        padding-block-start: var(--ak-c-button--PaddingTop);
        padding-block-end: var(--ak-c-button--PaddingBottom);
        padding-inline-start: var(--ak-c-button--PaddingLeft);
        padding-inline-end: var(--ak-c-button--PaddingRight);
        font-size: var(--ak-c-button--FontSize);
        font-weight: var(--ak-c-button--FontWeight);
        line-height: var(--ak-c-button--LineHeight);
        text-align: center;
        white-space: nowrap;
        user-select: none;
        border: 0;
        border-radius: var(--ak-c-button--BorderRadius);
        position: relative;
        font-family: var(--ak-c-button--FontFamily);
    }

    [part="button"]::after {
        position: absolute;
        inset-block-start: 0;
        inset-block-end: 0;
        inset-inline-start: 0;
        inset-inline-end: 0;
        pointer-events: none;
        content: "";
        border: var(--ak-c-button--after--BorderWidth) solid;
        border-color: var(--ak-c-button--after--BorderColor);
        border-radius: var(--ak-c-button--after--BorderRadius);
    }

    [part="anchor"] {
        padding-block-start: var(--ak-c-button--PaddingTop);
        padding-block-end: var(--ak-c-button--PaddingBottom);
        padding-inline-start: var(--ak-c-button--PaddingLeft);
        padding-inline-end: var(--ak-c-button--PaddingRight);
        font-size: var(--ak-c-button--FontSize);
        font-weight: var(--ak-c-button--FontWeight);
        line-height: var(--ak-c-button--LineHeight);
        text-align: center;
        white-space: nowrap;
        user-select: none;
        border: 0;
        border-radius: var(--ak-c-button--BorderRadius);
    }

    [part="anchor"]::after {
        position: absolute;
        inset-block-start: 0;
        inset-block-end: 0;
        inset-inline-start: 0;
        inset-inline-end: 0;
        pointer-events: none;
        content: "";
        border: var(--ak-c-button--after--BorderWidth) solid;
        border-color: var(--ak-c-button--after--BorderColor);
        border-radius: var(--ak-c-button--after--BorderRadius);
    }

    :host(:hover) {
        --ak-c-button--after--BorderWidth: var(--ak-c-button--hover--after--BorderWidth);
        text-decoration: none;
    }

    :host(:focus-within) {
        --ak-c-button--after--BorderWidth: var(--ak-c-button--focus--after--BorderWidth);
    }

    :host(:active) {
        --ak-c-button--after--BorderWidth: var(--ak-c-button--active--after--BorderWidth);
    }

    :host([block]) {
        display: block;
        width: 100%;
    }

    :host([block]) #main {
        width: 100%;
    }

    :host([small]) {
        --ak-c-button--FontSize: var(--ak-c-button--m-small--FontSize);
    }

    :host([size="sm"]) {
        --ak-c-button--FontSize: var(--ak-c-button--m-small--FontSize);
    }

    :host([size="lg"]) {
        --ak-c-button--PaddingTop: var(--ak-c-button--m-display-lg--PaddingTop);
        --ak-c-button--PaddingRight: var(--ak-c-button--m-display-lg--PaddingRight);
        --ak-c-button--PaddingBottom: var(--ak-c-button--m-display-lg--PaddingBottom);
        --ak-c-button--PaddingLeft: var(--ak-c-button--m-display-lg--PaddingLeft);
        --ak-c-button--FontWeight: var(--ak-c-button--m-display-lg--FontWeight);
        --ak-c-button--FontSize: var(--ak-c-button--m-link--m-display-lg--FontSize);
    }

    :host([narrow]) {
        --ak-c-button--PaddingTop: var(--ak-c-button--m-narrow--PaddingTop);
        --ak-c-button--PaddingRight: var(--ak-c-button--m-narrow--PaddingRight);
        --ak-c-button--PaddingBottom: var(--ak-c-button--m-narrow--PaddingBottom);
        --ak-c-button--PaddingLeft: var(--ak-c-button--m-narrow--PaddingLeft);
    }

    :host([variant="primary"]) #main {
        color: var(--ak-c-button--m-primary--Color);
        background-color: var(--ak-c-button--m-primary--BackgroundColor);
    }

    :host([variant="secondary"]) #main {
        --ak-c-button--after--BorderColor: var(--ak-c-button--m-secondary--after--BorderColor);
        color: var(--ak-c-button--m-secondary--Color);
        background-color: var(--ak-c-button--m-secondary--BackgroundColor);
    }

    :host([variant="tertiary"]) #main {
        --ak-c-button--after--BorderColor: var(--ak-c-button--m-tertiary--after--BorderColor);
        color: var(--ak-c-button--m-tertiary--Color);
        background-color: var(--ak-c-button--m-tertiary--BackgroundColor);
    }

    :host([variant="link"]) #main {
        --ak-c-button--disabled--BackgroundColor: var(
            --ak-c-button--m-link--disabled--BackgroundColor
        );
        --ak-c-button--disabled--Color: var(--ak-c-button--m-link--disabled--Color);
        color: var(--ak-c-button--m-link--Color);
        background-color: var(--ak-c-button--m-link--BackgroundColor);
    }

    :host([variant="plain"]) #main {
        --ak-c-button--disabled--Color: var(--ak-c-button--m-plain--disabled--Color);
        --ak-c-button--disabled--BackgroundColor: var(
            --ak-c-button--m-plain--disabled--BackgroundColor
        );
        color: var(--ak-c-button--m-plain--Color);
        background-color: var(--ak-c-button--m-plain--BackgroundColor);
    }

    :host([variant="control"]) #main {
        --ak-c-button--BorderRadius: var(--ak-c-button--m-control--BorderRadius);
        --ak-c-button--disabled--BackgroundColor: var(
            --ak-c-button--m-control--disabled--BackgroundColor
        );
        --ak-c-button--after--BorderWidth: var(--ak-c-button--m-control--after--BorderWidth);
        color: var(--ak-c-button--m-control--Color);
        background-color: var(--ak-c-button--m-control--BackgroundColor);
        --ak-c-button--after--BorderColor: var(--ak-c-button--m-control--after--BorderTopColor)
            var(--ak-c-button--m-control--after--BorderRightColor)
            var(--ak-c-button--m-control--after--BorderBottomColor)
            var(--ak-c-button--m-control--after--BorderLeftColor);
    }

    :host([variant="primary"]:hover) #main {
        --ak-c-button--m-primary--Color: var(--ak-c-button--m-primary--hover--Color);
        --ak-c-button--m-primary--BackgroundColor: var(
            --ak-c-button--m-primary--hover--BackgroundColor
        );
    }

    :host([variant="primary"]:focus-visible) #main {
        --ak-c-button--m-primary--Color: var(--ak-c-button--m-primary--focus--Color);
        --ak-c-button--m-primary--BackgroundColor: var(
            --ak-c-button--m-primary--focus--BackgroundColor
        );
    }

    :host([variant="primary"]:active) #main {
        --ak-c-button--m-primary--Color: var(--ak-c-button--m-primary--active--Color);
        --ak-c-button--m-primary--BackgroundColor: var(
            --ak-c-button--m-primary--active--BackgroundColor
        );
    }

    :host([variant="secondary"]:hover) #main {
        --ak-c-button--m-secondary--Color: var(--ak-c-button--m-secondary--hover--Color);
        --ak-c-button--m-secondary--BackgroundColor: var(
            --ak-c-button--m-secondary--hover--BackgroundColor
        );
        --ak-c-button--after--BorderColor: var(
            --ak-c-button--m-secondary--hover--after--BorderColor
        );
    }

    :host([variant="secondary"]:focus-visible) #main {
        --ak-c-button--m-secondary--Color: var(--ak-c-button--m-secondary--focus--Color);
        --ak-c-button--m-secondary--BackgroundColor: var(
            --ak-c-button--m-secondary--focus--BackgroundColor
        );
        --ak-c-button--after--BorderColor: var(
            --ak-c-button--m-secondary--focus--after--BorderColor
        );
    }

    :host([variant="tertiary"]:hover) #main {
        --ak-c-button--m-tertiary--Color: var(--ak-c-button--m-tertiary--hover--Color);
        --ak-c-button--m-tertiary--BackgroundColor: var(
            --ak-c-button--m-tertiary--hover--BackgroundColor
        );
        --ak-c-button--after--BorderColor: var(
            --ak-c-button--m-tertiary--hover--after--BorderColor
        );
    }

    :host([variant="tertiary"]:focus-visible) #main {
        --ak-c-button--m-tertiary--Color: var(--ak-c-button--m-tertiary--focus--Color);
        --ak-c-button--m-tertiary--BackgroundColor: var(
            --ak-c-button--m-tertiary--focus--BackgroundColor
        );
        --ak-c-button--after--BorderColor: var(
            --ak-c-button--m-tertiary--focus--after--BorderColor
        );
    }

    :host([variant="tertiary"]:active) #main {
        --ak-c-button--m-tertiary--Color: var(--ak-c-button--m-tertiary--active--Color);
        --ak-c-button--m-tertiary--BackgroundColor: var(
            --ak-c-button--m-tertiary--active--BackgroundColor
        );
        --ak-c-button--after--BorderColor: var(
            --ak-c-button--m-tertiary--active--after--BorderColor
        );
    }

    :host([variant="control"]:hover) #main {
        --ak-c-button--m-control--Color: var(--ak-c-button--m-control--hover--Color);
        --ak-c-button--m-control--BackgroundColor: var(
            --ak-c-button--m-control--hover--BackgroundColor
        );
        --ak-c-button--m-control--after--BorderBottomColor: var(
            --ak-c-button--m-control--hover--after--BorderBottomColor
        );
    }

    :host([variant="control"]:active) #main {
        --ak-c-button--m-control--Color: var(--ak-c-button--m-control--active--Color);
        --ak-c-button--m-control--BackgroundColor: var(
            --ak-c-button--m-control--active--BackgroundColor
        );
        --ak-c-button--m-control--after--BorderBottomColor: var(
            --ak-c-button--m-control--active--after--BorderBottomColor
        );
    }

    :host([variant="control"]:focus-visible) #main {
        --ak-c-button--m-control--Color: var(--ak-c-button--m-control--focus--Color);
        --ak-c-button--m-control--BackgroundColor: var(
            --ak-c-button--m-control--focus--BackgroundColor
        );
        --ak-c-button--m-control--after--BorderBottomColor: var(
            --ak-c-button--m-control--focus--after--BorderBottomColor
        );
    }

    :host([variant="plain"]:hover) #main {
        --ak-c-button--m-plain--Color: var(--ak-c-button--m-plain--hover--Color);
        --ak-c-button--m-plain--BackgroundColor: var(
            --ak-c-button--m-plain--hover--BackgroundColor
        );
    }

    :host([variant="plain"]:active) #main {
        --ak-c-button--m-plain--Color: var(--ak-c-button--m-plain--active--Color);
        --ak-c-button--m-plain--BackgroundColor: var(
            --ak-c-button--m-plain--active--BackgroundColor
        );
    }

    :host([variant="plain"]:focus-visible) #main {
        --ak-c-button--m-plain--Color: var(--ak-c-button--m-plain--focus--Color);
        --ak-c-button--m-plain--BackgroundColor: var(
            --ak-c-button--m-plain--focus--BackgroundColor
        );
    }

    :host([variant="secondary"][active]) #main {
        --ak-c-button--m-secondary--Color: var(--ak-c-button--m-secondary--active--Color);
        --ak-c-button--m-secondary--BackgroundColor: var(
            --ak-c-button--m-secondary--active--BackgroundColor
        );
        --ak-c-button--after--BorderColor: var(
            --ak-c-button--m-secondary--active--after--BorderColor
        );
    }

    :host([severity="danger"]) #main {
        color: var(--ak-c-button--m-danger--Color);
        background-color: var(--ak-c-button--m-danger--BackgroundColor);
    }

    :host([severity="warning"]) #main {
        color: var(--ak-c-button--m-warning--Color);
        background-color: var(--ak-c-button--m-warning--BackgroundColor);
    }

    :host([severity="danger"]:hover) #main {
        --ak-c-button--m-danger--Color: var(--ak-c-button--m-danger--hover--Color);
        --ak-c-button--m-danger--BackgroundColor: var(
            --ak-c-button--m-danger--hover--BackgroundColor
        );
    }

    :host([severity="danger"]:focus-visible) #main {
        --ak-c-button--m-danger--Color: var(--ak-c-button--m-danger--focus--Color);
        --ak-c-button--m-danger--BackgroundColor: var(
            --ak-c-button--m-danger--focus--BackgroundColor
        );
    }

    :host([severity="danger"]:active) #main {
        --ak-c-button--m-danger--Color: var(--ak-c-button--m-danger--active--Color);
        --ak-c-button--m-danger--BackgroundColor: var(
            --ak-c-button--m-danger--active--BackgroundColor
        );
    }

    :host([severity="warning"]:hover) #main {
        --ak-c-button--m-warning--Color: var(--ak-c-button--m-warning--hover--Color);
        --ak-c-button--m-warning--BackgroundColor: var(
            --ak-c-button--m-warning--hover--BackgroundColor
        );
    }

    :host([severity="warning"]:focus-visible) #main {
        --ak-c-button--m-warning--Color: var(--ak-c-button--m-warning--focus--Color);
        --ak-c-button--m-warning--BackgroundColor: var(
            --ak-c-button--m-warning--focus--BackgroundColor
        );
    }

    :host([severity="warning"]:active) #main {
        --ak-c-button--m-warning--Color: var(--ak-c-button--m-warning--active--Color);
        --ak-c-button--m-warning--BackgroundColor: var(
            --ak-c-button--m-warning--active--BackgroundColor
        );
    }

    :host([variant="secondary"][severity="danger"]):hover #main {
        --ak-c-button--m-secondary--m-danger--Color: var(
            --ak-c-button--m-secondary--m-danger--hover--Color
        );
        --ak-c-button--m-secondary--m-danger--BackgroundColor: var(
            --ak-c-button--m-secondary--m-danger--hover--BackgroundColor
        );
        --ak-c-button--after--BorderColor: var(
            --ak-c-button--m-secondary--m-danger--hover--after--BorderColor
        );
    }

    :host([variant="secondary"][severity="danger"]):focus-visible #main {
        --ak-c-button--m-secondary--m-danger--Color: var(
            --ak-c-button--m-secondary--m-danger--focus--Color
        );
        --ak-c-button--m-secondary--m-danger--BackgroundColor: var(
            --ak-c-button--m-secondary--m-danger--focus--BackgroundColor
        );
        --ak-c-button--after--BorderColor: var(
            --ak-c-button--m-secondary--m-danger--focus--after--BorderColor
        );
    }

    :host([variant="secondary"][severity="danger"]):active #main {
        --ak-c-button--m-secondary--m-danger--Color: var(
            --ak-c-button--m-secondary--m-danger--active--Color
        );
        --ak-c-button--m-secondary--m-danger--BackgroundColor: var(
            --ak-c-button--m-secondary--m-danger--active--BackgroundColor
        );
        --ak-c-button--after--BorderColor: var(
            --ak-c-button--m-secondary--m-danger--active--after--BorderColor
        );
    }

    :host([variant="link"][severity="danger"]):hover #main {
        --ak-c-button--m-link--m-danger--Color: var(--ak-c-button--m-link--m-danger--hover--Color);
        --ak-c-button--m-link--m-danger--BackgroundColor: var(
            --ak-c-button--m-link--m-danger--hover--BackgroundColor
        );
    }

    :host([variant="link"][severity="danger"]):focus-visible #main {
        --ak-c-button--m-link--m-danger--Color: var(--ak-c-button--m-link--m-danger--focus--Color);
        --ak-c-button--m-link--m-danger--BackgroundColor: var(
            --ak-c-button--m-link--m-danger--focus--BackgroundColor
        );
    }

    :host([variant="link"][severity="danger"]):active #main {
        --ak-c-button--m-link--m-danger--Color: var(--ak-c-button--m-link--m-danger--active--Color);
        --ak-c-button--m-link--m-danger--BackgroundColor: var(
            --ak-c-button--m-link--m-danger--active--BackgroundColor
        );
    }

    :host([variant="control"]) #main::after {
        border-radius: initial;
        --ak-c-button--after--BorderColor: var(--ak-c-button--m-control--after--BorderTopColor)
            var(--ak-c-button--m-control--after--BorderRightColor)
            var(--ak-c-button--m-control--after--BorderBottomColor)
            var(--ak-c-button--m-control--after--BorderLeftColor);
    }

    :host([variant="control"]):hover #main::after {
        border-block-end-width: var(--ak-c-button--m-control--hover--after--BorderBottomWidth);
    }

    :host([variant="control"]):active #main::after {
        border-block-end-width: var(--ak-c-button--m-control--active--after--BorderBottomWidth);
    }

    :host([variant="control"]):focus-visible #main::after {
        border-block-end-width: var(--ak-c-button--m-control--focus--after--BorderBottomWidth);
    }

    :host([variant="control"][expanded]) #main {
        --ak-c-button--m-control--Color: var(--ak-c-button--m-control--m-expanded--Color);
        --ak-c-button--m-control--BackgroundColor: var(
            --ak-c-button--m-control--m-expanded--BackgroundColor
        );
        --ak-c-button--m-control--after--BorderBottomColor: var(
            --ak-c-button--m-control--m-expanded--after--BorderBottomColor
        );
    }

    :host([variant="control"][expanded]) #main::after {
        border-block-end-width: var(--ak-c-button--m-control--m-expanded--after--BorderBottomWidth);
    }

    :host([icon-position="start"]) #main {
        margin-inline-end: var(--ak-c-button__icon--m-start--MarginRight);
    }

    :host([icon-position="end"]) #main {
        margin-inline-start: var(--ak-c-button__icon--m-end--MarginLeft);
    }

    :host:disabled,
    :host([disabled]) {
        color: var(--ak-c-button--disabled--Color);
        background-color: var(--ak-c-button--disabled--BackgroundColor);
    }

    :host:disabled #main,
    :host([disabled]) #main {
        pointer-events: none;
    }

    :host:disabled #main::after,
    :host([disabled]) #main::after {
        border-color: var(--ak-c-button--disabled--after--BorderColor);
    }

    :host([variant="link"]:not([inline])):hover #main {
        --ak-c-button--m-link--Color: var(--ak-c-button--m-link--hover--Color);
        --ak-c-button--m-link--BackgroundColor: var(--ak-c-button--m-link--hover--BackgroundColor);
    }

    :host([variant="link"]:not([inline])):focus-visible #main {
        --ak-c-button--m-link--Color: var(--ak-c-button--m-link--focus--Color);
        --ak-c-button--m-link--BackgroundColor: var(--ak-c-button--m-link--focus--BackgroundColor);
    }

    :host([variant="link"]:not([inline])):active #main {
        --ak-c-button--m-link--Color: var(--ak-c-button--m-link--active--Color);
        --ak-c-button--m-link--BackgroundColor: var(--ak-c-button--m-link--active--BackgroundColor);
    }

    :host([variant="link"][size="lg"]) {
        --ak-c-button--FontSize: var(--ak-c-button--m-link--m-display-lg--FontSize);
    }

    :host([variant="link"][inline]) #main {
        --ak-c-button--FontSize: var(--ak-c-button--m-link--m-inline--FontSize);
        --ak-c-button__progress--Left: var(--ak-c-button--m-link--m-inline__progress--Left);
        display: inline;
        padding-block-start: var(--ak-c-button--m-link--m-inline--PaddingTop);
        padding-block-end: var(--ak-c-button--m-link--m-inline--PaddingBottom);
        padding-inline-start: var(--ak-c-button--m-link--m-inline--PaddingLeft);
        padding-inline-end: var(--ak-c-button--m-link--m-inline--PaddingRight);
        text-align: start;
        white-space: normal;
        cursor: pointer;
    }

    :host([variant="link"][severity="danger"]) #main {
        --ak-c-button--m-danger--Color: var(--ak-c-button--m-link--m-danger--Color);
        --ak-c-button--m-danger--BackgroundColor: var(
            --ak-c-button--m-link--m-danger--BackgroundColor
        );
    }
`;

export default styles;
