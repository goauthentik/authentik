import { ERROR_CLASS, PROGRESS_CLASS, SUCCESS_CLASS } from "#common/constants";
import { PFSize } from "#common/enums";

import { AKElement } from "#elements/Base";
import { ifPresent } from "#elements/utils/attributes";
import { CustomEmitterElement } from "#elements/utils/eventEmitter";

import { Task, TaskStatus } from "@lit/task";
import { css, html } from "lit";
import { property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFSpinner from "@patternfly/patternfly/components/Spinner/spinner.css";

// `pointer-events: none` makes the button inaccessible during the processing phase.

const buttonStyles = [
    PFButton,
    PFSpinner,
    css`
        #spinner-button {
            transition: all var(--pf-c-button--m-progress--TransitionDuration) ease 0s;
        }
        #spinner-button.working {
            pointer-events: none;
        }

        .pf-c-button {
            &.pf-m-primary.pf-m-success {
                color: var(--pf-c-button--m-primary--Color) !important;
            }

            &.pf-m-secondary.pf-m-success {
                color: var(--pf-c-button--m-secondary--Color) !important;
            }
        }
    `,
];

const StatusMap = {
    [TaskStatus.INITIAL]: "",
    [TaskStatus.PENDING]: PROGRESS_CLASS,
    [TaskStatus.COMPLETE]: SUCCESS_CLASS,
    [TaskStatus.ERROR]: ERROR_CLASS,
} as const satisfies Record<TaskStatus, string>;

const SPINNER_TIMEOUT = 1000 * 1.5; // milliseconds

/**
 * BaseTaskButton
 *
 * This is an abstract base class for our four-state buttons. It provides the four basic events of
 * this class: click, success, failure, reset. Subclasses can override any of these event handlers,
 * but overriding onSuccess() or onFailure() means that you must either call `onComplete` if you
 * want to preserve the TaskButton's "reset after completion" semantics, or inside `onSuccess` and
 * `onFailure` call their `super.` equivalents.
 *
 */

export abstract class BaseTaskButton extends CustomEmitterElement(AKElement) {
    eventPrefix = "ak-button";

    static styles = [...buttonStyles];

    callAction!: () => Promise<unknown>;

    actionTask: Task;

    @property({ type: Boolean })
    public disabled = false;

    @property({ type: String })
    public label: string | null = null;

    constructor() {
        super();
        this.onSuccess = this.onSuccess.bind(this);
        this.onError = this.onError.bind(this);
        this.onClick = this.onClick.bind(this);
        this.actionTask = this.buildTask();
    }

    buildTask() {
        return new Task(this, {
            task: () => this.callAction(),
            args: () => [],
            autoRun: false,
            onComplete: (r: unknown) => this.onSuccess(r),
            onError: (r: unknown) => this.onError(r),
        });
    }

    onComplete() {
        setTimeout(() => {
            this.dispatchCustomEvent(`${this.eventPrefix}-reset`);
            // set-up for the next task...
            this.actionTask = this.buildTask();
            this.requestUpdate();
        }, SPINNER_TIMEOUT);
    }

    onSuccess(r: unknown) {
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
        // Don't accept clicks when a task is in progress..
        if (this.actionTask.status === TaskStatus.PENDING) {
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
            StatusMap[this.actionTask.status],
            this.actionTask.status === TaskStatus.INITIAL ? "" : "working",
        ]
            .join(" ")
            .trim();
    }

    render() {
        return html`<button
            id="spinner-button"
            part="spinner-button"
            class="pf-c-button pf-m-progress ${this.buttonClasses}"
            @click=${this.onClick}
            type="button"
            aria-label=${ifPresent(this.label)}
            aria-busy=${this.actionTask.status === TaskStatus.PENDING ? "true" : "false"}
            ?disabled=${this.disabled}
        >
            ${this.actionTask.render({
                pending: () => this.spinner,
            })}
            <slot></slot>
        </button>`;
    }
}

export default BaseTaskButton;
