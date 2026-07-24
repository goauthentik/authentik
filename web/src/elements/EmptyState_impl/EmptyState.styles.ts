/**
 * @file ShadowDOM CSS for the EmptyState component
 */

import { css } from "lit";

export const styles = css`
    root.css :host(:not([hidden])) {
        display: block;
    }

    [part="empty-state"] {
        display: flex;
        align-items: center;
        justify-content: center;
        padding-block-start: var(--ak-c-empty-state--PaddingTop);
        padding-block-end: var(--ak-c-empty-state--PaddingBottom);
        padding-inline-start: var(--ak-c-empty-state--PaddingLeft);
        padding-inline-end: var(--ak-c-empty-state--PaddingRight);
        text-align: center;
    }

    :host([size="xs"]) {
        --ak-c-empty-state--PaddingTop: var(--ak-c-empty-state--m-xs--PaddingTop);
        --ak-c-empty-state--PaddingRight: var(--ak-c-empty-state--m-xs--PaddingRight);
        --ak-c-empty-state--PaddingBottom: var(--ak-c-empty-state--m-xs--PaddingBottom);
        --ak-c-empty-state--PaddingLeft: var(--ak-c-empty-state--m-xs--PaddingLeft);
        --ak-c-empty-state__title-text--FontSize: var(
            --ak-c-empty-state--m-xs__title-text--FontSize
        );
        --ak-c-empty-state__content--MaxWidth: var(--ak-c-empty-state--m-xs__content--MaxWidth);
        --ak-c-empty-state__icon--MarginBottom: var(--ak-c-empty-state--m-xs__icon--MarginBottom);
        --ak-c-empty-state__body--MarginTop: var(--ak-c-empty-state--m-xs__body--MarginTop);
        --ak-c-empty-state--body--FontSize: var(--ak-c-empty-state--m-xs__body--FontSize);
        --ak-c-empty-state__footer--MarginTop: var(--ak-c-empty-state--m-xs__footer--MarginTop);
    }

    :host([size="sm"]) {
        --ak-c-empty-state__content--MaxWidth: var(--ak-c-empty-state--m-sm__content--MaxWidth);
    }

    :host([size="lg"]) {
        --ak-c-empty-state__content--MaxWidth: var(--ak-c-empty-state--m-lg__content--MaxWidth);
    }

    :host([size="xl"]) {
        --ak-c-empty-state__body--MarginTop: var(--ak-c-empty-state--m-xl__body--MarginTop);
        --ak-c-empty-state--body--FontSize: var(--ak-c-empty-state--m-xl__body--FontSize);
        --ak-c-empty-state__icon--MarginBottom: var(--ak-c-empty-state--m-xl__icon--MarginBottom);
        --ak-c-empty-state__icon--FontSize: var(--ak-c-empty-state--m-xl__icon--FontSize);
        --ak-c-empty-state__title-text--FontSize: var(
            --ak-c-empty-state--m-xl__title-text--FontSize
        );
        --ak-c-empty-state__title-text--LineHeight: var(
            --ak-c-empty-state--m-xl__title-text--LineHeight
        );
    }

    :host([compact]) {
        --ak-c-empty-state--PaddingTop: var(--ak-c-empty-state--m-compact--PaddingTop);
        --ak-c-empty-state--PaddingRight: var(--ak-c-empty-state--m-compact--PaddingRight);
        --ak-c-empty-state--PaddingBottom: var(--ak-c-empty-state--m-compact--PaddingBottom);
        --ak-c-empty-state--PaddingLeft: var(--ak-c-empty-state--m-compact--PaddingLeft);
        --ak-c-empty-state--m-xs--PaddingTop: var(--ak-c-empty-state--m-compact--m-xs--PaddingTop);
        --ak-c-empty-state--m-xs--PaddingRight: var(
            --ak-c-empty-state--m-compact--m-xs--PaddingRight
        );
        --ak-c-empty-state--m-xs--PaddingBottom: var(
            --ak-c-empty-state--m-compact--m-xs--PaddingBottom
        );
        --ak-c-empty-state--m-xs--PaddingLeft: var(
            --ak-c-empty-state--m-compact--m-xs--PaddingLeft
        );
        --ak-c-empty-state__icon--MarginBottom: var(
            --ak-c-empty-state--m-compact__icon--MarginBottom
        );
        --ak-c-empty-state--m-xs__icon--MarginBottom: var(
            --ak-c-empty-state--m-compact--m-xs__icon--MarginBottom
        );
        --ak-c-empty-state--m-xl__icon--MarginBottom: var(
            --ak-c-empty-state--m-compact--m-xl__icon--MarginBottom
        );
        --ak-c-empty-state__body--MarginTop: var(--ak-c-empty-state--m-compact__body--MarginTop);
        --ak-c-empty-state--m-xs__body--MarginTop: var(
            --ak-c-empty-state--m-compact--m-xs__body--MarginTop
        );
        --ak-c-empty-state--m-xl__body--MarginTop: var(
            --ak-c-empty-state--m-compact--m-xl__body--MarginTop
        );
        --ak-c-empty-state__footer--MarginTop: var(
            --ak-c-empty-state--m-compact__footer--MarginTop
        );
        --ak-c-empty-state--m-xs__footer--MarginTop: var(
            --ak-c-empty-state--m-compact--m-xs__footer--MarginTop
        );
        --ak-c-empty-state__footer--RowGap: var(--ak-c-empty-state--m-compact__footer--RowGap);
    }

    :host([full-height]) {
        height: 100%;
    }

    [part="content"] {
        max-width: var(--ak-c-empty-state__content--MaxWidth);
    }

    [part="icon"] {
        margin-block-end: var(--ak-c-empty-state__icon--MarginBottom);
        font-size: var(--ak-c-empty-state__icon--FontSize);
        line-height: 1;
        color: var(--ak-c-empty-state__icon--Color);
    }

    [part="body"] {
        margin-block-start: var(--ak-c-empty-state__body--MarginTop);
        font-size: var(--ak-c-empty-state--body--FontSize);
        color: var(--ak-c-empty-state__body--Color);
    }

    [part="primary"] {
        display: flex;
        flex-direction: column;
        row-gap: var(--ak-c-empty-state__footer--RowGap);
        align-items: center;
        margin-block-start: var(--ak-c-empty-state__footer--MarginTop);
    }

    [part~="actions"] {
        display: flex;
        flex-wrap: wrap;
        gap: var(--ak-c-empty-state__actions--RowGap) var(--ak-c-empty-state__actions--ColumnGap);
        justify-content: center;
    }

    [part="heading"] {
        font-family: var(--ak-c-empty-state__title-text--FontFamily);
        font-size: var(--ak-c-empty-state__title-text--FontSize);
        font-weight: var(--ak-c-empty-state__title-text--FontWeight);
        line-height: var(--ak-c-empty-state__title-text--LineHeight);
    }
`;

export default styles;
