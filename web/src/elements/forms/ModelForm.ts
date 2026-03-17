import "#elements/EmptyState";

import { AKRefreshEvent } from "#common/events";

import { listen } from "#elements/decorators/listen";
import { Form } from "#elements/forms/Form";
import { SlottedTemplateResult } from "#elements/types";

import { ConsoleLogger } from "#logger/browser";

import { html } from "lit";
import { property } from "lit/decorators.js";

/**
 * A base form that automatically tracks the server-side object (instance)
 * that we're interested in. Handles loading and tracking of the instance.
 *
 * @template T The type of the model instance.
 * @template PKT The type of the primary key of the model instance.
 *
 * @prop {T} instance - The current instance being edited or viewed.
 * @prop {PKT} instancePk - The primary key of the instance to load.
 */
export abstract class ModelForm<
    T extends object = object,
    PKT extends string | number = string | number,
> extends Form<T> {
    protected logger = ConsoleLogger.prefix(`model-form/${this.tagName.toLowerCase()}`);

    /**
     * An overridable method for loading an instance.
     *
     * @param pk The primary key of the instance to load.
     * @returns A promise that resolves to the loaded instance.
     */
    protected abstract loadInstance(pk: PKT): Promise<T>;

    /**
     * An overridable method for loading any data, beyond the instance.
     *
     * @see {@linkcode loadInstance}
     * @returns A promise that resolves when the data has been loaded.
     */
    protected async load(): Promise<void> {
        return Promise.resolve();
    }

    @property({ attribute: "pk", converter: { fromAttribute: (value) => value as PKT } })
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

    #instancePk: PKT | null = null;

    public get instancePk(): PKT | null {
        return this.#instancePk;
    }

    // Keep track if we've loaded the model instance
    #initialLoad = false;

    // Keep track if we've done the general data loading of load()
    #initialDataLoad = false;

    #loading = false;

    @property({ attribute: false })
    instance?: T = this.defaultInstance;

    get defaultInstance(): T | undefined {
        return undefined;
    }

    @listen(AKRefreshEvent, {
        target: null,
    })
    protected refresh = async () => {
        await new Promise((resolve) => requestAnimationFrame(resolve));

        if (!this.#instancePk) return;

        const viewportVisible = this.isInViewport || !this.viewportCheck;

        if (!viewportVisible) {
            this.logger.debug(`Instance not in viewport, skipping refresh`);
            return;
        }

        return this.loadInstance(this.#instancePk).then((instance) => {
            this.instance = instance;
        });
    };

    public override reset(): void {
        super.reset();

        this.instance = undefined;
        this.#initialLoad = false;
        this.#initialDataLoad = false;

        this.requestUpdate();
    }

    protected override renderVisible(): SlottedTemplateResult {
        if ((this.#instancePk && !this.instance) || !this.#initialDataLoad) {
            return html`<ak-empty-state loading></ak-empty-state>`;
        }
        return super.renderVisible();
    }

    protected override render(): SlottedTemplateResult {
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
