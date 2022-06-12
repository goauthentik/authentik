import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import AKGlobal from "../authentik.css";
import PFTreeView from "@patternfly/patternfly/components/TreeView/tree-view.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { EVENT_REFRESH } from "../constants";
import { setURLParams } from "./router/RouteMatch";

export interface TreeViewItem {
    id: string;
    label: string;
    childItems: TreeViewItem[];
    parent?: TreeViewItem;
    level: number;
}

@customElement("ak-treeview-node")
export class TreeViewNode extends LitElement {
    @property({ attribute: false })
    item?: TreeViewItem;

    @property({ type: Boolean })
    open = false;

    @property({ attribute: false })
    host?: TreeView;

    @property()
    path = "";

    @property()
    separator = "";

    get openable(): boolean {
        return (this.item?.childItems || []).length > 0;
    }

    get fullPath(): string {
        const pathItems = [];
        let item = this.item;
        while (item) {
            pathItems.push(item.id);
            item = item.parent;
        }
        return pathItems.reverse().join(this.separator);
    }

    protected createRenderRoot(): Element {
        return this;
    }

    firstUpdated(): void {
        const pathSegments = this.path.split(this.separator);
        // Ignore the last item as that shouldn't be expanded
        pathSegments.pop();
        if (pathSegments.length < (this.item?.level || 0)) return;
        if (pathSegments[this.item?.level || 0] == this.item?.id) {
            this.open = true;
        }
        if (this.path === this.fullPath && this.host !== undefined) {
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
                            path=${this.path}
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
export class TreeView extends LitElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFTreeView, AKGlobal];
    }

    @property({ type: Array })
    items: string[] = [];

    @property()
    path = "";

    @state()
    activeNode?: TreeViewNode;

    separator = "/";

    createNode(path: string[], tree: TreeViewItem[], level: number): TreeViewItem {
        const id = path.shift();
        const idx = tree.findIndex((e: TreeViewItem) => {
            return e.id == id;
        });
        if (idx < 0) {
            const item: TreeViewItem = {
                id: id || "",
                label: id || "",
                childItems: [],
                level: level,
            };
            tree.push(item);
            if (path.length !== 0) {
                const child = this.createNode(path, tree[tree.length - 1].childItems, level + 1);
                child.parent = item;
            }
            return item;
        } else {
            return this.createNode(path, tree[idx].childItems, level + 1);
        }
    }

    parse(data: string[]): TreeViewItem[] {
        const tree: TreeViewItem[] = [];
        for (let i = 0; i < data.length; i++) {
            const path: string = data[i];
            const split: string[] = path.split(this.separator);
            // Start with level 1 as we have a pseudo-item for level 0
            this.createNode(split, tree, 1);
        }
        return tree;
    }

    render(): TemplateResult {
        const result = this.parse(this.items);
        return html`<div class="pf-c-tree-view pf-m-guides">
            <ul class="pf-c-tree-view__list" role="tree">
                <!-- @ts-ignore -->
                <ak-treeview-node
                    .item=${{
                        id: "",
                        label: t`Root`,
                        childItems: result,
                        level: 0,
                    } as TreeViewItem}
                    path=""
                    ?open=${true}
                    separator=${this.separator}
                    .host=${this}
                ></ak-treeview-node>
            </ul>
        </div>`;
    }
}
