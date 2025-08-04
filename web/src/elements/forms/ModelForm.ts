import "#elements/EmptyState";

import { EVENT_REFRESH } from "#common/constants";

import { Form } from "#elements/forms/Form";
import { SlottedTemplateResult } from "#elements/types";

import { html, TemplateResult } from "lit";
import { property } from "lit/decorators.js";

/**
 * Model form
 *
 * A base form that automatically tracks the server-side object (instance)
 * that we're interested in.  Handles loading and tracking of the instance.
 */

export abstract class ModelForm<T, PKT extends string | number> extends Form<T> {
    protected abstract loadInstance(pk: PKT): Promise<T>;

    protected async load(): Promise<void> {
        return Promise.resolve();
    }

    @property({ attribute: false })
    public set instancePk(value: PKT) {
        this.#instancePk = value;

        if (this.viewportCheck && !this.isInViewport) {
            return;
        }

        if (this.#loading) {
            return;
        }

        this.#loading = true;

        this.load().then(() => {
            this.loadInstance(value).then((instance) => {
                this.instance = instance;
                this.#loading = false;
                this.requestUpdate();
            });
        });
    }

    #instancePk?: PKT;

    // Keep track if we've loaded the model instance
    #initialLoad = false;

    // Keep track if we've done the general data loading of load()
    #initialDataLoad = false;

    #loading = false;

    @property({ attribute: false })
    public instance?: T = this.defaultInstance;

    public get defaultInstance(): T | undefined {
        return undefined;
    }

    public constructor() {
        super();

        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.#instancePk) return;
            this.loadInstance(this.#instancePk).then((instance) => {
                this.instance = instance;
            });
        });
    }

    public override reset(): void {
        this.instance = undefined;
        this.#initialLoad = false;
    }

    protected override renderVisible(): TemplateResult {
        if ((this.#instancePk && !this.instance) || !this.#initialDataLoad) {
            return html`<ak-empty-state loading></ak-empty-state>`;
        }
        return super.renderVisible();
    }

    public override render(): SlottedTemplateResult {
        // if we're in viewport now and haven't loaded AND have a PK set, load now
        // Or if we don't check for viewport in some cases
        const viewportVisible = this.isInViewport || !this.viewportCheck;
        if (this.#instancePk && !this.#initialLoad && viewportVisible) {
            this.instancePk = this.#instancePk;
            this.#initialLoad = true;
        } else if (!this.#initialDataLoad && viewportVisible) {
            // else if since if the above case triggered that will also call this.load(), so
            // ensure we don't load again
            this.load().then(() => {
                this.#initialDataLoad = true;
                // Class attributes changed in this.load() might not be @property()
                // or @state() so let's trigger a re-render to be sure we get updated
                this.requestUpdate();
            });
        }

        return super.render();
    }
}
