import { EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";
import { setURLParams } from "#elements/router/RouteMatch";
import { ifPresent } from "#elements/utils/attributes";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFTreeView from "@patternfly/patternfly/components/TreeView/tree-view.css";

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

    protected createRenderRoot() {
        return this;
    }

    firstUpdated(): void {
        const pathSegments = this.activePath.split(this.separator);
        const level = this.item?.level || 0;
        // Ignore the last item as that shouldn't be expanded
        pathSegments.pop();
        if (pathSegments[level] === this.item?.id) {
            this.open = true;
        }
        if (this.activePath === this.fullPath && this.host !== undefined) {
            this.host.activeNode = this;
        }
    }

    #selectionListener = () => {
        if (this.host) {
            this.host.activeNode = this;
        }
        setURLParams({ path: this.fullPath });
        this.dispatchEvent(
            new CustomEvent(EVENT_REFRESH, {
                bubbles: true,
                composed: true,
                detail: {
                    path: this.fullPath,
                },
            }),
        );
    };

    render(): TemplateResult {
        const shouldRenderChildren = (this.item?.childItems || []).length > 0 && this.open;
        const itemLabel = this.item?.label || msg("Unnamed");
        const current = this.host?.activeNode === this;

        return html`
            <li
                class="pf-c-tree-view__list-item ${this.open ? "pf-m-expanded" : ""}"
                role="treeitem"
                aria-expanded=${ifPresent(this.openable, this.open ? "true" : "false")}
                aria-label=${itemLabel}
                aria-selected=${current ? "true" : "false"}
                tabindex="0"
            >
                <div class="pf-c-tree-view__content">
                    <div
                        class="pf-c-tree-view__node ${current ? "pf-m-current" : ""}"
                        @click=${this.#selectionListener}
                    >
                        <div class="pf-c-tree-view__node-container">
                            ${this.openable
                                ? html` <button
                                      type="button"
                                      aria-label=${ifPresent(
                                          this.openable,
                                          this.open
                                              ? msg(str`Collapse "${itemLabel}"`)
                                              : msg(str`Expand "${itemLabel}"`),
                                      )}
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
                                : nothing}
                            <span class="pf-c-tree-view__node-icon">
                                <i
                                    class="fas ${this.open ? "fa-folder-open" : "fa-folder"}"
                                    aria-hidden="true"
                                ></i>
                            </span>
                            <button
                                type="button"
                                aria-label=${msg(str`Select "${itemLabel}"`)}
                                @click=${this.#selectionListener}
                                class="pf-c-tree-view__node-text"
                            >
                                ${itemLabel}
                            </button>
                        </div>
                    </div>
                </div>
                <ul
                    class="pf-c-tree-view__list"
                    ?hidden=${!shouldRenderChildren}
                    role="group"
                    aria-label=${msg(str`Items of "${itemLabel}"`)}
                >
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
    static styles: CSSResult[] = [PFTreeView];

    @property({ type: String })
    public label: string | null = null;

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
            return e.id === id;
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
        }
        return this.createNode(path, parentItem.childItems[idx], level + 1);
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
            <ul class="pf-c-tree-view__list" role="tree" aria-label=${ifPresent(this.label)}>
                <ak-treeview-node
                    .item=${rootItem}
                    activePath=${this.activePath}
                    open
                    separator=${this.separator}
                    .host=${this}
                ></ak-treeview-node>
            </ul>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-treeview": TreeView;
        "ak-treeview-node": TreeViewNode;
    }
}
