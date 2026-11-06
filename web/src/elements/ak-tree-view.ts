import { TreeView } from "./TreeView/TreeView.component";

export { TreeView };

window.customElements.define("ak-tree-view", TreeView);

declare global {
    interface HTMLElementTagNameMap {
        "ak-tree-view": TreeView;
    }
}
