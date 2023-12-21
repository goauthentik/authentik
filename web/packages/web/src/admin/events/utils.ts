import { EventWithContext } from "@goauthentik/common/events";
import { KeyUnknown } from "@goauthentik/elements/forms/Form";

import { TemplateResult, html } from "lit";

export function EventGeo(event: EventWithContext): TemplateResult {
    let geo: KeyUnknown | undefined = undefined;
    if (Object.hasOwn(event.context, "geo")) {
        geo = event.context.geo as KeyUnknown;
        const parts = [geo.city, geo.country, geo.continent].filter(
            (v) => v !== "" && v !== undefined,
        );
        return html`${parts.join(", ")}`;
    }
    return html``;
}
