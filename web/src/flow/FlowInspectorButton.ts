import { AKElement } from "#elements/Base";
import { listen } from "#elements/decorators/listen";
import { CapabilitiesEnum, WithCapabilitiesConfig } from "#elements/mixins/capabilities";

import { AKFlowAdvanceEvent, AKFlowInspectorChangeEvent } from "#flow/events";

import { msg } from "@lit/localize";
import { html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";

// Custom implementation because there are rules for when to show this.

@customElement("ak-flow-inspector-button")
export class FlowInspectorButton extends WithCapabilitiesConfig(AKElement) {
    public static readonly styles = [PFButton];

    @property({ type: Boolean, reflect: true })
    public open = false;

    @state()
    private available = false;

    @state()
    private loaded = false;

    @listen(AKFlowInspectorChangeEvent)
    private onInspectorToggle = (ev: AKFlowInspectorChangeEvent) => {
        this.open = ev.open;
    };

    public override connectedCallback() {
        super.connectedCallback();
        const inspector = new URLSearchParams(window.location.search).get("inspector");
        this.available = this.can(CapabilitiesEnum.CanDebug) || inspector !== undefined;
        this.open = inspector === "" || inspector === "open";
    }

    protected toggle = () => {
        this.open = !this.open;
    };

    public override render() {
        return this.open || !this.available
            ? nothing
            : html`<button
                  aria-label=${this.open ? msg("Close flow inspector") : msg("Open flow inspector")}
                  aria-expanded=${this.open ? "true" : "false"}
                  class="inspector-toggle pf-c-button pf-m-primary"
                  aria-controls="flow-inspector"
                  @click=${this.toggle}
              >
                  <i class="fa fa-search-plus" aria-hidden="true"></i>
              </button>`;
    }

    public override firstUpdated(changed: PropertyValues<this>) {
        super.firstUpdated(changed);
        if (this.open) {
            window.dispatchEvent(new AKFlowAdvanceEvent());
        }
    }

    // Only load the inspector if the user requests it. It should hydrate automatically
    public override updated(changed: PropertyValues<this>) {
        super.updated(changed);
        if (changed.has("open") && this.open && !this.loaded) {
            import("#flow/FlowInspector").then(() => {
                this.loaded = true;
            });
        }
        const drawer = document.getElementById("flow-drawer");
        if (changed.has("open") && drawer) {
            drawer.classList.toggle("pf-m-expanded", this.open);
            drawer.classList.toggle("pf-m-collapsed", !this.open);
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-inspector-button": FlowInspectorButton;
    }
}
