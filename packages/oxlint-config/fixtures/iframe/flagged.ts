import { html, nothing } from "lit";

declare const body: string;
declare const url: string;
declare const tokens: string;
declare const enabled: boolean;
declare const frame: HTMLIFrameElement;

// Each case holds exactly one iframe or DOM call, so the expected count is the number of cases.

export const srcdoc = html`<iframe srcdoc=${body}></iframe>`;
export const srcdocProperty = html`<iframe .srcdoc=${body}></iframe>`;
export const src = html`<iframe src=${url}></iframe>`;
export const upperCase = html`<IFRAME SRC=${url}></IFRAME>`;

export const escape = html`<iframe sandbox="allow-scripts allow-same-origin" src=${url}></iframe>`;
export const escapeReordered = html`<iframe sandbox="allow-same-origin  ALLOW-SCRIPTS" src=${url}></iframe>`;

export const boundSandbox = html`<iframe sandbox=${tokens} src=${url}></iframe>`;
export const partlyBoundSandbox = html`<iframe sandbox="allow-forms ${tokens}" src=${url}></iframe>`;
export const booleanSandbox = html`<iframe ?sandbox=${enabled} src=${url}></iframe>`;
export const propertySandbox = html`<iframe .sandbox=${tokens} src=${url}></iframe>`;

export const multiLine = html`<div>
    <iframe
        @load=${() => frame.focus()}
        src=${url}
    ></iframe>
</div>`;

export const nested = html`<div>${enabled ? html`<iframe src=${url}></iframe>` : nothing}</div>`;

export const created = document.createElement("iframe");

frame.srcdoc = body;
frame.setAttribute("srcdoc", body);
