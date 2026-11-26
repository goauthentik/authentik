import { css, html } from "lit";

declare const body: string;
declare const url: string;
declare const frame: HTMLIFrameElement;

export const srcdoc = html`<iframe sandbox srcdoc=${body}></iframe>`;
export const emptySandbox = html`<iframe sandbox="" src=${url}></iframe>`;
export const scripts = html`<iframe sandbox="allow-scripts allow-forms" src=${url}></iframe>`;
export const sameOrigin = html`<iframe sandbox="allow-same-origin" srcdoc=${body}></iframe>`;

export const customElement = html`<ak-iframe src=${url}></ak-iframe>`;
export const comment = html`<!-- <iframe src="https://example.com"></iframe> -->`;
export const styles = css`
    iframe {
        border: 0;
    }
`;

export const div = document.createElement("div");

frame.src = url;
frame.setAttribute("src", url);
