/**
 * @file ShadowDOM CSS for the Breadcrumbs component
 */

import { css } from "lit";

export const styles = css`
    :host {
        display: inline-block;
    }

    /* Base breadcrumbs container styles */
    [part="breadcrumbs"],
    [part="list"] {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: var(--ak-c-breadcrumb__item--Gap);
    }

    [part="item"] {
        display: flex;
        align-items: baseline;
        font-size: var(--ak-c-breadcrumb__item--FontSize);
        font-weight: var(--ak-c-breadcrumb__item--FontWeight);
        line-height: var(--ak-c-breadcrumb__item--LineHeight);
        white-space: nowrap;
        list-style: none;
    }

    [part="item"]:not(:last-child)::after {
        color: var(--pf-global--Color--200);
        padding-left: var(--ak-c-breadcrumb__item--Gap);
        content: ">";
    }

    [part="link"] {
        font-size: inherit;
        font-weight: var(--ak-c-breadcrumb__link--FontWeight);
        line-height: inherit;
        color: var(--ak-c-breadcrumb__link--Color);
        text-decoration: var(--ak-c-breadcrumb__link--TextDecoration);
        word-break: break-word;
        background-color: var(--ak-c-breadcrumb__link--BackgroundColor);
    }

    [part="link"]:hover {
        --ak-c-breadcrumb__link--Color: var(--ak-c-breadcrumb__link--hover--Color);
        --ak-c-breadcrumb__link--TextDecoration: var(
            --ak-c-breadcrumb__link--hover--TextDecoration
        );
    }
`;

export default styles;
