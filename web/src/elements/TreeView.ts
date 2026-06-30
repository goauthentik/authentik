import PFTreeView from "@patternfly/patternfly/components/TreeView/tree-view.css";

import { EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";
import { setURLParams } from "#elements/router/RouteMatch";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { msg, str } from "@lit/localize";
import { CSSResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

//#region Tree View Node

export interface TreeViewItem {
    id: string | null;
    label: string;
    childItems: TreeViewItem[];
    parent?: TreeViewItem;
    level: number;
}

@customElement("ak-treeview-node")
export class TreeViewNode extends AKElement {
    @property({ attribute: false })
    public item: TreeViewItem | null = null;

    @property({ type: Boolean })
    public open = false;

    @property({ attribute: false })
    public host: TreeView | null = null;

    @property({ type: String, attribute: "active-path" })
    public activePath = "";

    @property({ type: String })
    public separator = "";

    public get openable(): boolean {
        return (this.item?.childItems || []).length > 0;
    }

    public get fullPath(): string {
        const pathItems = [];
        let item = this.item;

        while (item) {
            if (item.id) {
                pathItems.push(item.id);
            }
            item = item.parent || null;
        }

        return pathItems.reverse().join(this.separator);
    }

    protected createRenderRoot() {
        return this;
    }

    protected override firstUpdated(): void {
        const pathSegments = this.activePath.split(this.separator);
        const level = this.item?.level || 0;
        // Ignore the last item as that shouldn't be expanded
        pathSegments.pop();

        if (pathSegments[level] === this.item?.id) {
            this.open = true;
        }

        if (this.activePath === this.fullPath && this.host) {
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

    protected override render(): SlottedTemplateResult {
        const shouldRenderChildren = (this.item?.childItems || []).length > 0 && this.open;
        const itemLabel = this.item?.label || msg("Unnamed");
        const current = this.host?.activeNode === this;

        return html`<li
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
                            : null}
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
                        active-path=${this.activePath}
                        separator=${this.separator}
                        .host=${this.host}
                    ></ak-treeview-node>`;
                })}
            </ul>
        </li> `;
    }
}

//#endregion

//#region Tree View

@customElement("ak-treeview")
export class TreeView extends AKElement {
    static styles: CSSResult[] = [PFTreeView];

    @property({ type: String })
    public label: string | null = null;

    @property({ type: Array })
    public items: string[] = [];

    @property({ type: String, attribute: "default-active-path", useDefault: true })
    public defaultActivePath = "";

    @property({ attribute: false })
    public activeNode: TreeViewNode | null = null;

    protected separator = "/";

    public createNode(path: string[], parentItem: TreeViewItem, level: number): TreeViewItem {
        const id = path.shift() || null;
        const idx = parentItem.childItems.findIndex((item) => item.id === id);

        if (idx < 0) {
            const item: TreeViewItem = {
                id,
                label: id || "",
                childItems: [],
                level,
                parent: parentItem,
            };

            parentItem.childItems.push(item);

            if (path.length) {
                const child = this.createNode(path, item, level + 1);
                child.parent = item;
            }

            return item;
        }

        return this.createNode(path, parentItem.childItems[idx], level + 1);
    }

    protected parse(data: string[]): TreeViewItem {
        const rootItem: TreeViewItem = {
            id: null,
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

    protected override render(): SlottedTemplateResult {
        const rootItem = this.parse(this.items);

        return html`<div class="pf-c-tree-view pf-m-guides">
            <ul class="pf-c-tree-view__list" role="tree" aria-label=${ifPresent(this.label)}>
                <ak-treeview-node
                    .item=${rootItem}
                    active-path=${this.defaultActivePath}
                    open
                    separator=${this.separator}
                    .host=${this}
                ></ak-treeview-node>
            </ul>
        </div>`;
    }
}

//#endregion

declare global {
    interface HTMLElementTagNameMap {
        "ak-treeview": TreeView;
        "ak-treeview-node": TreeViewNode;
    }
}
