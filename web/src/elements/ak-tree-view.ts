import { akTreeView, type TreeViewProps } from "./TreeView/TreeView.builder";
import { TreeView } from "./TreeView/TreeView.component";

export { akTreeView, TreeView };
export type { TreeViewProps };

window.customElements.define("ak-tree-view", TreeView);

declare global {
    interface HTMLElementTagNameMap {
        "ak-tree-view": TreeView;
    }
}
