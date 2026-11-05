import { msg } from "@lit/localize";
import { ReactiveController, ReactiveControllerHost } from "lit";

/** Brief button feedback only; email rate limits are enforced by the server. */
export class ResendFeedback implements ReactiveController {
    public state: "idle" | "sending" | "sent" = "idle";
    #timer?: ReturnType<typeof setTimeout>;
    #generation = 0;

    constructor(private host: Pick<ReactiveControllerHost, "addController" | "requestUpdate">) {
        host.addController(this);
    }

    get label(): string {
        if (this.state === "sending") {
            return msg("Sending…", { id: "email-otp.resend.label.sending" });
        }

        if (this.state === "sent") {
            return msg("Code sent", { id: "email-otp.resend.success" });
        }

        return msg("Resend code", { id: "email-otp.resend.label" });
    }

    #setState(state: typeof this.state) {
        this.state = state;
        this.host.requestUpdate();
    }

    async run(send: () => Promise<boolean>): Promise<void> {
        if (this.state !== "idle") return;
        const generation = this.#generation;
        this.#setState("sending");
        let sent = false;

        try {
            sent = await send();
        } catch {
            // The flow host displays API errors. Do not claim a failed send succeeded.
        }

        if (generation !== this.#generation) return;
        this.#setState(sent ? "sent" : "idle");

        if (sent) {
            this.#timer = setTimeout(() => {
                this.#timer = undefined;
                this.#setState("idle");
            }, 15000);
        }
    }

    hostDisconnected() {
        this.#generation++;
        clearTimeout(this.#timer);
        this.#timer = undefined;
        this.#setState("idle");
    }
}
