import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { AKElement } from "@goauthentik/elements/Base";
import { setURLParams } from "@goauthentik/elements/router/RouteMatch";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFTreeView from "@patternfly/patternfly/components/TreeView/tree-view.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export interface TreeViewItem {
    id?: string;
    label: string;
    childItems: TreeViewItem[];
    parent?: TreeViewItem;
    level: number;
}

@customElement("ak-treeview-node")
export class TreeViewNode extends AKElement {
    @property({ attribute: false })
    item?: TreeViewItem;

    @property({ type: Boolean })
    open = false;

    @property({ attribute: false })
    host?: TreeView;

    @property()
    activePath = "";

    @property()
    separator = "";

    get openable(): boolean {
        return (this.item?.childItems || []).length > 0;
    }

    get fullPath(): string {
        const pathItems = [];
        let item = this.item;
        while (item) {
            if (item.id) {
                pathItems.push(item.id);
            }
            item = item.parent;
        }
        return pathItems.reverse().join(this.separator);
    }

    protected createRenderRoot(): Element {
        return this;
    }

    firstUpdated(): void {
        const pathSegments = this.activePath.split(this.separator);
        const level = this.item?.level || 0;
        // Ignore the last item as that shouldn't be expanded
        pathSegments.pop();
        if (pathSegments[level] == this.item?.id) {
            this.open = true;
        }
        if (this.activePath === this.fullPath && this.host !== undefined) {
            this.host.activeNode = this;
        }
    }

    render(): TemplateResult {
        const shouldRenderChildren = (this.item?.childItems || []).length > 0 && this.open;
        return html`
            <li
                class="pf-c-tree-view__list-item ${this.open ? "pf-m-expanded" : ""}"
                role="treeitem"
                tabindex="0"
            >
                <div class="pf-c-tree-view__content">
                    <button
                        class="pf-c-tree-view__node ${this.host?.activeNode === this
                            ? "pf-m-current"
                            : ""}"
                        @click=${() => {
                            if (this.host) {
                                this.host.activeNode = this;
                            }
                            setURLParams({ path: this.fullPath });
                            this.dispatchEvent(
                                new CustomEvent(EVENT_REFRESH, {
                                    bubbles: true,
                                    composed: true,
                                }),
                            );
                        }}
                    >
                        <div class="pf-c-tree-view__node-container">
                            ${this.openable
                                ? html` <button
                                      class="pf-c-tree-view__node-toggle"
                                      @click=${(e: Event) => {
                                          if (this.openable) {
                                              this.open = !this.open;
                                              e.stopPropagation();
                                          }
                                      }}
                                  >
                                      <span class="pf-c-tree-view__node-toggle-icon">
                                          <i class="fas fa-angle-right" aria-hidden="true"></i>
                                      </span>
                                  </button>`
                                : html``}
                            <span class="pf-c-tree-view__node-icon">
                                <i
                                    class="fas ${this.open ? "fa-folder-open" : "fa-folder"}"
                                    aria-hidden="true"
                                ></i>
                            </span>
                            <span class="pf-c-tree-view__node-text">${this.item?.label}</span>
                        </div>
                    </button>
                </div>
                <ul class="pf-c-tree-view__list" role="group" ?hidden=${!shouldRenderChildren}>
                    ${this.item?.childItems.map((item) => {
                        return html`<ak-treeview-node
                            .item=${item}
                            activePath=${this.activePath}
                            separator=${this.separator}
                            .host=${this.host}
                        ></ak-treeview-node>`;
                    })}
                </ul>
            </li>
        `;
    }
}

@customElement("ak-treeview")
export class TreeView extends AKElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFTreeView];
    }

    @property({ type: Array })
    items: string[] = [];

    @property()
    activePath = "";

    @state()
    activeNode?: TreeViewNode;

    separator = "/";

    createNode(path: string[], parentItem: TreeViewItem, level: number): TreeViewItem {
        const id = path.shift();
        const idx = parentItem.childItems.findIndex((e: TreeViewItem) => {
            return e.id == id;
        });
        if (idx < 0) {
            const item: TreeViewItem = {
                id: id,
                label: id || "",
                childItems: [],
                level: level,
                parent: parentItem,
            };
            parentItem.childItems.push(item);
            if (path.length !== 0) {
                const child = this.createNode(path, item, level + 1);
                child.parent = item;
            }
            return item;
        } else {
            const child = this.createNode(path, parentItem.childItems[idx], level + 1);
            return child;
        }
    }

    parse(data: string[]): TreeViewItem {
        const rootItem: TreeViewItem = {
            id: undefined,
            label: msg("Root"),
            childItems: [],
            level: -1,
        };
        for (let i = 0; i < data.length; i++) {
            const path: string = data[i];
            const split: string[] = path.split(this.separator);
            this.createNode(split, rootItem, 0);
        }
        return rootItem;
    }

    render(): TemplateResult {
        const rootItem = this.parse(this.items);
        return html`<div class="pf-c-tree-view pf-m-guides">
            <ul class="pf-c-tree-view__list" role="tree">
                <ak-treeview-node
                    .item=${rootItem}
                    activePath=${this.activePath}
                    ?open=${true}
                    separator=${this.separator}
                    .host=${this}
                ></ak-treeview-node>
            </ul>
        </div>`;
    }
}
