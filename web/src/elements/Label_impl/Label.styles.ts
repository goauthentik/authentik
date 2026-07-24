/**
 * @file ShadowDOM CSS for the Label component
 */

import { css } from "lit";

export const styles = css`
    :host {
        display: inline-flex;
        align-items: center;
        align-content: center;
        position: relative;
        width: fit-content;
    }

    :host([compact]) {
        --ak-c-label--PaddingTop: var(--ak-c-label--m-compact--PaddingTop);
        --ak-c-label--PaddingRight: var(--ak-c-label--m-compact--PaddingRight);
        --ak-c-label--PaddingBottom: var(--ak-c-label--m-compact--PaddingBottom);
        --ak-c-label--PaddingLeft: var(--ak-c-label--m-compact--PaddingLeft);
        --ak-c-label--FontSize: var(--ak-c-label--m-compact--FontSize);
        --ak-c-label--m-editable--TextDecorationOffset: var(
            --ak-c-label--m-compact--m-editable--TextDecorationOffset
        );
    }

    :host([color="blue"]),
    .status-blue {
        --ak-c-label--BackgroundColor: var(--ak-c-label--m-blue--BackgroundColor);
        --ak-c-label__icon--Color: var(--ak-c-label--m-blue__icon--Color);
        --ak-c-label__content--Color: var(--ak-c-label--m-blue__content--Color);
        --ak-c-label__content--before--BorderColor: var(
            --ak-c-label--m-blue__content--before--BorderColor
        );
        --ak-c-label__content--link--hover--before--BorderColor: var(
            --ak-c-label--m-blue__content--link--hover--before--BorderColor
        );
        --ak-c-label__content--link--focus--before--BorderColor: var(
            --ak-c-label--m-blue__content--link--focus--before--BorderColor
        );
        --ak-c-label--m-outline__content--Color: var(
            --ak-c-label--m-outline--m-blue__content--Color
        );
        --ak-c-label--m-outline__content--before--BorderColor: var(
            --ak-c-label--m-outline--m-blue__content--before--BorderColor
        );
        --ak-c-label--m-outline__content--link--hover--before--BorderColor: var(
            --ak-c-label--m-outline--m-blue__content--link--hover--before--BorderColor
        );
        --ak-c-label--m-outline__content--link--focus--before--BorderColor: var(
            --ak-c-label--m-outline--m-blue__content--link--focus--before--BorderColor
        );
        --ak-c-label--m-editable__content--before--BorderColor: var(
            --ak-c-label--m-blue__content--before--BorderColor
        );
        --ak-c-label--m-editable__content--hover--before--BorderColor: var(
            --ak-c-label--m-blue__content--before--BorderColor
        );
        --ak-c-label--m-editable__content--focus--before--BorderColor: var(
            --ak-c-label--m-blue__content--before--BorderColor
        );
    }

    :host([color="green"]),
    .status-green {
        --ak-c-label--BackgroundColor: var(--ak-c-label--m-green--BackgroundColor);
        --ak-c-label__icon--Color: var(--ak-c-label--m-green__icon--Color);
        --ak-c-label__content--Color: var(--ak-c-label--m-green__content--Color);
        --ak-c-label__content--before--BorderColor: var(
            --ak-c-label--m-green__content--before--BorderColor
        );
        --ak-c-label__content--link--hover--before--BorderColor: var(
            --ak-c-label--m-green__content--link--hover--before--BorderColor
        );
        --ak-c-label__content--link--focus--before--BorderColor: var(
            --ak-c-label--m-green__content--link--focus--before--BorderColor
        );
        --ak-c-label--m-outline__content--Color: var(
            --ak-c-label--m-outline--m-green__content--Color
        );
        --ak-c-label--m-outline__content--before--BorderColor: var(
            --ak-c-label--m-outline--m-green__content--before--BorderColor
        );
        --ak-c-label--m-outline__content--link--hover--before--BorderColor: var(
            --ak-c-label--m-outline--m-green__content--link--hover--before--BorderColor
        );
        --ak-c-label--m-outline__content--link--focus--before--BorderColor: var(
            --ak-c-label--m-outline--m-green__content--link--focus--before--BorderColor
        );
        --ak-c-label--m-editable__content--before--BorderColor: var(
            --ak-c-label--m-green__content--before--BorderColor
        );
        --ak-c-label--m-editable__content--hover--before--BorderColor: var(
            --ak-c-label--m-green__content--before--BorderColor
        );
        --ak-c-label--m-editable__content--focus--before--BorderColor: var(
            --ak-c-label--m-green__content--before--BorderColor
        );
    }

    :host([color="orange"]),
    .status-orange {
        --ak-c-label--BackgroundColor: var(--ak-c-label--m-orange--BackgroundColor);
        --ak-c-label__icon--Color: var(--ak-c-label--m-orange__icon--Color);
        --ak-c-label__content--Color: var(--ak-c-label--m-orange__content--Color);
        --ak-c-label__content--before--BorderColor: var(
            --ak-c-label--m-orange__content--before--BorderColor
        );
        --ak-c-label__content--link--hover--before--BorderColor: var(
            --ak-c-label--m-orange__content--link--hover--before--BorderColor
        );
        --ak-c-label__content--link--focus--before--BorderColor: var(
            --ak-c-label--m-orange__content--link--focus--before--BorderColor
        );
        --ak-c-label--m-outline__content--Color: var(
            --ak-c-label--m-outline--m-orange__content--Color
        );
        --ak-c-label--m-outline__content--before--BorderColor: var(
            --ak-c-label--m-outline--m-orange__content--before--BorderColor
        );
        --ak-c-label--m-outline__content--link--hover--before--BorderColor: var(
            --ak-c-label--m-outline--m-orange__content--link--hover--before--BorderColor
        );
        --ak-c-label--m-outline__content--link--focus--before--BorderColor: var(
            --ak-c-label--m-outline--m-orange__content--link--focus--before--BorderColor
        );
        --ak-c-label--m-editable__content--before--BorderColor: var(
            --ak-c-label--m-orange__content--before--BorderColor
        );
        --ak-c-label--m-editable__content--hover--before--BorderColor: var(
            --ak-c-label--m-orange__content--before--BorderColor
        );
        --ak-c-label--m-editable__content--focus--before--BorderColor: var(
            --ak-c-label--m-orange__content--before--BorderColor
        );
    }

    :host([color="red"]),
    .status-red {
        --ak-c-label--BackgroundColor: var(--ak-c-label--m-red--BackgroundColor);
        --ak-c-label__icon--Color: var(--ak-c-label--m-red__icon--Color);
        --ak-c-label__content--Color: var(--ak-c-label--m-red__content--Color);
        --ak-c-label__content--before--BorderColor: var(
            --ak-c-label--m-red__content--before--BorderColor
        );
        --ak-c-label__content--link--hover--before--BorderColor: var(
            --ak-c-label--m-red__content--link--hover--before--BorderColor
        );
        --ak-c-label__content--link--focus--before--BorderColor: var(
            --ak-c-label--m-red__content--link--focus--before--BorderColor
        );
        --ak-c-label--m-outline__content--Color: var(
            --ak-c-label--m-outline--m-red__content--Color
        );
        --ak-c-label--m-outline__content--before--BorderColor: var(
            --ak-c-label--m-outline--m-red__content--before--BorderColor
        );
        --ak-c-label--m-outline__content--link--hover--before--BorderColor: var(
            --ak-c-label--m-outline--m-red__content--link--hover--before--BorderColor
        );
        --ak-c-label--m-outline__content--link--focus--before--BorderColor: var(
            --ak-c-label--m-outline--m-red__content--link--focus--before--BorderColor
        );
        --ak-c-label--m-editable__content--before--BorderColor: var(
            --ak-c-label--m-red__content--before--BorderColor
        );
        --ak-c-label--m-editable__content--hover--before--BorderColor: var(
            --ak-c-label--m-red__content--before--BorderColor
        );
        --ak-c-label--m-editable__content--focus--before--BorderColor: var(
            --ak-c-label--m-red__content--before--BorderColor
        );
    }

    :host([color="purple"]),
    .status-purple {
        --ak-c-label--BackgroundColor: var(--ak-c-label--m-purple--BackgroundColor);
        --ak-c-label__icon--Color: var(--ak-c-label--m-purple__icon--Color);
        --ak-c-label__content--Color: var(--ak-c-label--m-purple__content--Color);
        --ak-c-label__content--before--BorderColor: var(
            --ak-c-label--m-purple__content--before--BorderColor
        );
        --ak-c-label__content--link--hover--before--BorderColor: var(
            --ak-c-label--m-purple__content--link--hover--before--BorderColor
        );
        --ak-c-label__content--link--focus--before--BorderColor: var(
            --ak-c-label--m-purple__content--link--focus--before--BorderColor
        );
        --ak-c-label--m-outline__content--Color: var(
            --ak-c-label--m-outline--m-purple__content--Color
        );
        --ak-c-label--m-outline__content--before--BorderColor: var(
            --ak-c-label--m-outline--m-purple__content--before--BorderColor
        );
        --ak-c-label--m-outline__content--link--hover--before--BorderColor: var(
            --ak-c-label--m-outline--m-purple__content--link--hover--before--BorderColor
        );
        --ak-c-label--m-outline__content--link--focus--before--BorderColor: var(
            --ak-c-label--m-outline--m-purple__content--link--focus--before--BorderColor
        );
        --ak-c-label--m-editable__content--before--BorderColor: var(
            --ak-c-label--m-purple__content--before--BorderColor
        );
        --ak-c-label--m-editable__content--hover--before--BorderColor: var(
            --ak-c-label--m-purple__content--before--BorderColor
        );
        --ak-c-label--m-editable__content--focus--before--BorderColor: var(
            --ak-c-label--m-purple__content--before--BorderColor
        );
    }

    :host([color="cyan"]),
    .status-cyan {
        --ak-c-label--BackgroundColor: var(--ak-c-label--m-cyan--BackgroundColor);
        --ak-c-label__icon--Color: var(--ak-c-label--m-cyan__icon--Color);
        --ak-c-label__content--Color: var(--ak-c-label--m-cyan__content--Color);
        --ak-c-label__content--before--BorderColor: var(
            --ak-c-label--m-cyan__content--before--BorderColor
        );
        --ak-c-label__content--link--hover--before--BorderColor: var(
            --ak-c-label--m-cyan__content--link--hover--before--BorderColor
        );
        --ak-c-label__content--link--focus--before--BorderColor: var(
            --ak-c-label--m-cyan__content--link--focus--before--BorderColor
        );
        --ak-c-label--m-outline__content--Color: var(
            --ak-c-label--m-outline--m-cyan__content--Color
        );
        --ak-c-label--m-outline__content--before--BorderColor: var(
            --ak-c-label--m-outline--m-cyan__content--before--BorderColor
        );
        --ak-c-label--m-outline__content--link--hover--before--BorderColor: var(
            --ak-c-label--m-outline--m-cyan__content--link--hover--before--BorderColor
        );
        --ak-c-label--m-outline__content--link--focus--before--BorderColor: var(
            --ak-c-label--m-outline--m-cyan__content--link--focus--before--BorderColor
        );
        --ak-c-label--m-editable__content--before--BorderColor: var(
            --ak-c-label--m-cyan__content--before--BorderColor
        );
        --ak-c-label--m-editable__content--hover--before--BorderColor: var(
            --ak-c-label--m-cyan__content--before--BorderColor
        );
        --ak-c-label--m-editable__content--focus--before--BorderColor: var(
            --ak-c-label--m-cyan__content--before--BorderColor
        );
    }

    :host([color="gold"]),
    .status-gold {
        --ak-c-label--BackgroundColor: var(--ak-c-label--m-gold--BackgroundColor);
        --ak-c-label__icon--Color: var(--ak-c-label--m-gold__icon--Color);
        --ak-c-label__content--Color: var(--ak-c-label--m-gold__content--Color);
        --ak-c-label__content--before--BorderColor: var(
            --ak-c-label--m-gold__content--before--BorderColor
        );
        --ak-c-label__content--link--hover--before--BorderColor: var(
            --ak-c-label--m-gold__content--link--hover--before--BorderColor
        );
        --ak-c-label__content--link--focus--before--BorderColor: var(
            --ak-c-label--m-gold__content--link--focus--before--BorderColor
        );
        --ak-c-label--m-outline__content--Color: var(
            --ak-c-label--m-outline--m-gold__content--Color
        );
        --ak-c-label--m-outline__content--before--BorderColor: var(
            --ak-c-label--m-outline--m-gold__content--before--BorderColor
        );
        --ak-c-label--m-outline__content--link--hover--before--BorderColor: var(
            --ak-c-label--m-outline--m-gold__content--link--hover--before--BorderColor
        );
        --ak-c-label--m-outline__content--link--focus--before--BorderColor: var(
            --ak-c-label--m-outline--m-gold__content--link--focus--before--BorderColor
        );
        --ak-c-label--m-editable__content--before--BorderColor: var(
            --ak-c-label--m-gold__content--before--BorderColor
        );
        --ak-c-label--m-editable__content--hover--before--BorderColor: var(
            --ak-c-label--m-gold__content--before--BorderColor
        );
        --ak-c-label--m-editable__content--focus--before--BorderColor: var(
            --ak-c-label--m-gold__content--before--BorderColor
        );
    }

    :host(:not([color])),
    :host([color="gray"]),
    :host([color="grey"]),
    .status-gray,
    .status-grey {
        --pf-c-label--BackgroundColor: var(--pf-c-label--m-gray--BackgroundColor);
        --pf-c-label__icon--Color: var(--pf-c-label--m-gray__icon--Color);
        --pf-c-label__content--Color: var(--pf-c-label--m-gray__content--Color);
        --pf-c-label__content--before--BorderColor: var(
            --pf-c-label--m-gray__content--before--BorderColor
        );
        --pf-c-label__content--link--hover--before--BorderColor: var(
            --pf-c-label--m-gray__content--link--hover--before--BorderColor
        );
        --pf-c-label__content--link--focus--before--BorderColor: var(
            --pf-c-label--m-gray__content--link--focus--before--BorderColor
        );
    }

    :host([outline]) {
        --ak-c-label__content--Color: var(--ak-c-label--m-outline__content--Color);
        --ak-c-label__content--before--BorderWidth: var(
            --ak-c-label--m-outline__content--before--BorderWidth
        );
        --ak-c-label__content--before--BorderColor: var(
            --ak-c-label--m-outline__content--before--BorderColor
        );
        --ak-c-label--BackgroundColor: var(--ak-c-label--m-outline--BackgroundColor);
        --ak-c-label--m-editable__content--before--BorderColor: var(
            --ak-c-label--m-outline__content--before--BorderColor
        );
        --ak-c-label--m-editable__content--hover--before--BorderColor: var(
            --ak-c-label--m-outline__content--before--BorderColor
        );
        --ak-c-label--m-editable__content--focus--before--BorderColor: var(
            --ak-c-label--m-outline__content--before--BorderColor
        );
    }

    ::slotted(*) {
        margin: 0;
    }

    [part="label"] {
        align-items: center;
        align-items: items;
        background-color: var(--ak-c-label--BackgroundColor);
        border-radius: var(--ak-c-label--BorderRadius);
        border: 0;
        color: var(--ak-c-label__content--Color);
        display: inline-flex;
        font-size: var(--ak-c-label--FontSize);
        max-width: var(--ak-c-label__content--MaxWidth);
        overflow: hidden;
        padding: var(--ak-c-label--PaddingTop) var(--ak-c-label--PaddingRight)
            var(--ak-c-label--PaddingBottom) var(--ak-c-label--PaddingLeft);
        position: relative;
        text-align: center;
        white-space: nowrap;
    }

    [part="label"]::before {
        position: absolute;
        inset: 0;
        pointer-events: none;
        content: "";
        background-color: var(--ak-c-label__content--BackgroundColor);
        border: var(--ak-c-label__content--before--BorderWidth) solid
            var(--ak-c-label__content--before--BorderColor);
        border-radius: var(--ak-c-label--BorderRadius);
    }

    :host([utility]) [part="label"],
    :host([utility]) [part="label"]:hover,
    :host([utility]) [part="label"]:focus {
        padding: 0;
        cursor: pointer;
        background-color: transparent;
        border: none;
    }

    :host([utility]) [part="label"]:hover {
        --ak-c-label__content--before--BorderWidth: var(
            --ak-c-label__content--link--hover--before--BorderWidth
        );
        --ak-c-label__content--before--BorderColor: var(
            --ak-c-label__content--link--hover--before--BorderColor
        );
    }

    :host([utility]) [part="label"]:focus {
        --ak-c-label__content--before--BorderWidth: var(
            --ak-c-label__content--link--focus--before--BorderWidth
        );
        --ak-c-label__content--before--BorderColor: var(
            --ak-c-label__content--link--focus--before--BorderColor
        );
    }

    [part="text"] {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        max-width: var(--ak-c-label__text--MaxWidth);
    }

    [part="icon"].has-content {
        display: flex;
        align-content: center;
        margin-inline-end: var(--ak-c-label__icon--MarginRight);
        color: var(--ak-c-label__icon--Color);
    }
`;

export default styles;
