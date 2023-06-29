import { ERROR_CLASS, PROGRESS_CLASS, SUCCESS_CLASS } from "@goauthentik/common/constants";
import { AKElement } from "@goauthentik/elements/Base";
import { PFSize } from "@goauthentik/elements/Spinner";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { Task, TaskStatus } from "@lit-labs/task";
import { css, html } from "lit";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFSpinner from "@patternfly/patternfly/components/Spinner/spinner.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

const buttonStyles = [
    PFBase,
    PFButton,
    PFSpinner,
    css`
        #spinner-button {
            transition: all var(--pf-c-button--m-progress--TransitionDuration) ease 0s;
        }
        #spinner-button.working {
            pointer-events: none;
        }
    `,
];

const StatusMap = new Map<TaskStatus, string>([
    [TaskStatus.INITIAL, ""],
    [TaskStatus.PENDING, PROGRESS_CLASS],
    [TaskStatus.COMPLETE, SUCCESS_CLASS],
    [TaskStatus.ERROR, ERROR_CLASS],
]);

const SPINNER_TIMEOUT = 1000 * 1.5; // milliseconds

export abstract class BaseTaskButton extends CustomEmitterElement(AKElement) {
    eventPrefix = "ak-button";

    static get styles() {
        return buttonStyles;
    }

    callAction!: () => Promise<unknown>;

    actionTask: Task;

    constructor() {
        super();
        this.onSuccess = this.onSuccess.bind(this);
        this.onError = this.onError.bind(this);
        this.onClick = this.onClick.bind(this);
        this.actionTask = new Task(this, {
            task: () => this.callAction(),
            args: () => [],
            autoRun: false,
            onComplete: (r: unknown) => this.onSuccess(r),
            onError: (r: unknown) => this.onError(r),
        });
    }

    onComplete() {
        setTimeout(() => {
            this.actionTask.status = TaskStatus.INITIAL;
            this.dispatchCustomEvent(`${this.eventPrefix}-reset`);
            this.requestUpdate();
        }, SPINNER_TIMEOUT);
    }

    onSuccess(r: unknown) {
        console.log("Emitting:", `${this.eventPrefix}-success`, r);
        this.dispatchCustomEvent(`${this.eventPrefix}-success`, {
            result: r,
        });
        this.onComplete();
    }

    onError(error: unknown) {
        this.dispatchCustomEvent(`${this.eventPrefix}-failure`, {
            error,
        });
        this.onComplete();
    }

    onClick() {
        if (this.actionTask.status !== TaskStatus.INITIAL) {
            return;
        }
        this.dispatchCustomEvent(`${this.eventPrefix}-click`);
        this.actionTask.run();
    }

    private spinner = html`<span class="pf-c-button__progress">
        <ak-spinner size=${PFSize.Medium}></ak-spinner>
    </span>`;

    get buttonClasses() {
        return [
            ...this.classList,
            StatusMap.get(this.actionTask.status),
            this.actionTask.status === TaskStatus.INITIAL ? "" : "working",
        ]
            .join(" ")
            .trim();
    }

    render() {
        return html`<button
            id="spinner-button"
            class="pf-c-button pf-m-progress ${this.buttonClasses}"
            @click=${this.onClick}
        >
            ${this.actionTask.render({ pending: () => this.spinner })}
            <slot></slot>
        </button>`;
    }
}

export default BaseTaskButton;
