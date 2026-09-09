import AKDrawer from "./ak-drawer.styles";
import { DrawerResizeController } from "./drawerResizeController";

import { html, LitElement, nothing, PropertyValues } from "lit";
import { property } from "lit/decorators.js";

export class DrawerExpandRequest extends Event {
    static readonly eventName = "ak-drawer-expand-request";
    expanded: boolean | null = null;

    constructor(expanded: boolean | null = null) {
        super(DrawerExpandRequest.eventName, { bubbles: true, composed: true });
        this.expanded = expanded;
    }
}

export class AkDrawer extends LitElement {
    static readonly styles = [AKDrawer];

    @property({ type: Boolean })
    public resizable = false;

    @property({ type: Boolean, reflect: true })
    public expanded = false;

    @property({ type: Boolean, reflect: true })
    public resizing = false;

    @property({ type: String, reflect: true })
    public width = "33";

    private resize = new DrawerResizeController(this);

    onDrawerRequest = (ev: DrawerExpandRequest) => {
        ev.stopPropagation();
        this.expanded = ev.expanded === null ? !this.expanded : ev.expanded;
    };

    constructor() {
        super();
        this.addEventListener(DrawerExpandRequest.eventName, this.onDrawerRequest);
    }

    public override render() {
        return html`
            <div class="ak-v2-c-drawer" part="drawer">
                <div class="ak-v2-c-drawer__main" part="drawer-main">
                    <div class="ak-v2-c-drawer__content" part="drawer-content">
                        <div class="ak-v2-c-drawer__body" part="drawer-body">
                            <slot></slot>
                        </div>
                    </div>
                    <div class="ak-v2-c-drawer__panel" part="drawer-panel">
                        ${this.resizable
                            ? html` <div
                                  class="ak-v2-c-drawer__splitter"
                                  part="drawer-splitter"
                                  @mousedown=${this.resize.handleMouseDown}
                                  @keydown=${this.resize.handleKeyDown}
                                  @touchstart=${this.resize.handleTouchStart}
                                  role="separator"
                                  tabindex="0"
                              >
                                  <div
                                      class="ak-v2-c-drawer__splitter-handle"
                                      aria-hidden="true"
                                  ></div>
                              </div>`
                            : nothing}
                        <div class="ak-v2-c-drawer__panel-main" part="drawer-panel-main">
                            <slot name="panel"></slot>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    public override updated(changed: PropertyValues<this>) {
        super.updated(changed);

        // Simulate the behavior of summary/details, another disclosure pattern.
        const expanded = changed.get("expanded");
        if (expanded !== undefined) {
            const expandedMsg = (i: boolean) => (i ? "open" : "closed");
            this.dispatchEvent(
                new ToggleEvent("toggle", {
                    newState: expandedMsg(this.expanded),
                    oldState: expandedMsg(expanded),
                }),
            );
        }
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        [DrawerExpandRequest.eventName]: DrawerExpandRequest;
    }
}
