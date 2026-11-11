import { AKElement } from "#elements/Base";

import { css, html, nothing } from "lit";
import { customElement } from "lit/decorators.js";
import { property } from "lit/decorators/property.js";

export const bookmarkStates = ["hidden", "marked", "unmarked"] as const;

export type BookmarkState = (typeof bookmarkStates)[number];

const hollowBookmark = html`<!-- © fontawesome. CC-BY-4.0 licensed --><svg
        xmlns="http://www.w3.org/2000/svg"
        data-icon-name="bookmark"
        height="512"
        width="384"
        viewBox="0 0 384 512"
    >
        <path
            d="M336 0H48C21.49 0 0 21.49 0 48v464l192-112 192 112V48c0-26.51-21.49-48-48-48zm0 428.43l-144-84-144 84V54a6 6 0 0 1 6-6h276c3.314 0 6 2.683 6 5.996V428.43z"
        />
    </svg>`;

const solidBookmark = html`<!-- © fontawesome. CC-BY-4.0 licensed --><svg
        xmlns="http://www.w3.org/2000/svg"
        data-icon-name="bookmark"
        height="512"
        width="384"
        viewBox="0 0 384 512"
    >
        <path d="M0 512V48C0 21.49 21.49 0 48 0h288c26.51 0 48 21.49 48 48v464L192 400 0 512z" />
    </svg>`;

const Styles = css`
    :host {
        display: inline-block;
    }

    [part="bookmark"] {
        transform: translateY(-20%);
        display: inline-block;
        padding-left: 0.25em;
    }

    [part="bookmark"] svg {
        transition: var(--pf-global--TransitionDuration);
        height: 1.25ex;
        width: fit-content;
    }

    [part="bookmark"] svg path {
        stroke: var(--pf-c-content--Color);
        fill: var(--pf-c-content--Color);
    }

    :host(:hover) [part="bookmark"] svg {
        scale: 1.1;
    }

    [part="bookmark"][data-state="marked"] svg path {
        stroke: var(--ak-accent);
        fill: var(--ak-accent);
    }

    :host(:hover) [part="bookmark"] svg path {
        stroke: var(--pf-global--link--Color);
        fill: var(--pf-global--link--Color);
    }
`;

@customElement("ak-bookmark")
export class Bookmark extends AKElement {
    static readonly styles = [Styles];

    @property({ type: String })
    state: BookmarkState = "hidden";

    public override render() {
        return this.state === "hidden"
            ? nothing
            : html`<div part="bookmark" data-state=${this.state}>
                  ${this.state === "marked" ? solidBookmark : hollowBookmark}
              </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-bookmark": Bookmark;
    }
}
