import { html } from "lit";

import "./ApplicationEmptyState";

export default {
    title: "ApplicationEmptyState",
};

export const OrdinaryUser = () =>
    html`<div style="background: #fff; padding: 4em">
        <ak-library-application-empty-list></ak-library-application-empty-list>
    </div> `;

export const AdminUser = () =>
    html`<div style="background: #fff; padding: 4em">
        <ak-library-application-empty-list isadmin></ak-library-application-empty-list>
    </div> `;
