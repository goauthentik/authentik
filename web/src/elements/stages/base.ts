import { LitElement } from "lit-element";
import { FlowExecutor } from "../../pages/generic/FlowExecutor";

export class BaseStage extends LitElement {

    host?: FlowExecutor;

    submit(e: Event): void {
        e.preventDefault();
        const form = new FormData(this.shadowRoot?.querySelector("form") || undefined);
        this.host?.submit(form);
    }
}
