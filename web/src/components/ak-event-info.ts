// import { akEventInfo, type EventInfoProps } from "./EventInfo/EventInfo.builder";
import { EventInfo } from "./EventInfo/EventInfo.component";

export { EventInfo };

window.customElements.define("ak-event-info", EventInfo);

declare global {
    interface HTMLElementTagNameMap {
        "ak-event-info": EventInfo;
    }
}
