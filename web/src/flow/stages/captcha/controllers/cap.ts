import { CaptchaController } from "#flow/stages/captcha/controllers/CaptchaController";
import {
    CapErrorEvent,
    CapSolveEvent,
    type CapWidgetElement,
} from "#flow/stages/captcha/controllers/events";
import { CaptchaVendor, CaptchaVendorGlobal } from "#flow/stages/captcha/shared";

export class CapController extends CaptchaController {
    public static override readonly vendor = CaptchaVendor.cap;

    public static readonly globalName = CaptchaVendorGlobal[CaptchaVendor.cap];

    public static readonly scriptType = "module";

    protected static override logPrefix = "cap";

    public static override isAvailable(): boolean {
        return customElements.get(CapController.globalName) !== undefined;
    }

    #widget: CapWidgetElement | null = null;

    #solveListener = ({ detail }: CapSolveEvent) => {
        this.host.onTokenChange(detail.token);
    };

    #errorListener = ({ detail }: CapErrorEvent) => {
        this.host.error = detail.message;
    };

    public mount = async (container: HTMLElement): Promise<void> => {
        // Cap ships as a custom element rather than a render API, so the script may still be
        // upgrading when the stage mounts.
        await customElements.whenDefined("cap-widget");

        const widget = document.createElement("cap-widget") as CapWidgetElement;

        widget.setAttribute("data-cap-api-endpoint", this.host.challenge?.siteKey ?? "");
        widget.addEventListener(CapSolveEvent.eventName, this.#solveListener);
        widget.addEventListener(CapErrorEvent.eventName, this.#errorListener);

        container.appendChild(widget);
        this.#widget = widget;

        this.host.onWidgetLoad();
    };

    public execute = async (): Promise<void> => {
        throw new Error("Cap requires interactive mode.");
    };

    public reset = async (): Promise<void> => {
        const container = this.#widget?.parentElement;

        if (!container) {
            this.logger.warn("Skipping reset: no widget rendered");
            return;
        }

        this.unmount();

        await this.mount(container);
    };

    public override unmount(): void {
        if (!this.#widget) return;

        this.#widget.removeEventListener(CapSolveEvent.eventName, this.#solveListener);
        this.#widget.removeEventListener(CapErrorEvent.eventName, this.#errorListener);
        this.#widget.remove();
        this.#widget = null;
    }
}
