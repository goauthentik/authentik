import "#elements/EmptyState";

import { EVENT_REFRESH } from "#common/constants";

import { Form } from "#elements/forms/Form";
import { SlottedTemplateResult } from "#elements/types";

import { html } from "lit";
import { property } from "lit/decorators.js";

/**
 * A base form that automatically tracks the server-side object (instance)
 * that we're interested in. Handles loading and tracking of the instance.
 */
export abstract class ModelForm<T, PKT extends string | number> extends Form<T> {
    //#region Protected Methods

    /**
     * An overridable method to create a default instance when no PK is given.
     *
     * @returns A default instance of T, or null if not implemented.
     * @abstract
     */
    protected createDefaultInstance?(): T | null;

    //#region Public Properties

    @property({ attribute: "pk" })
    public set instancePk(value: PKT) {
        this.#instancePk = value;

        if (this.#loading) {
            return;
        }

        this.#loading = true;

        this.load?.().then(() =>
            this.loadInstance(value).then((instance) => {
                this.instance = instance;
                this.#loading = false;

                this.requestUpdate();
            }),
        );
    }

    public get instancePk(): PKT | undefined {
        return this.#instancePk;
    }

    #instancePk?: PKT;

    // Keep track if we've loaded the model instance
    #initialLoad = false;

    // Keep track if we've done the general data loading of load()
    #initialDataLoad = false;

    #loading = false;

    @property({ attribute: false })
    public instance: T | null = this.createDefaultInstance?.() ?? null;

    get defaultInstance(): T | null {
        return null;
    }

    //#endregion

    //#region Lifecycle

    /**
     * An overridable method for loading an instance.
     *
     * @param pk The primary key of the instance to load.
     * @abstract
     * @returns A promise that resolves to the loaded instance.
     */
    protected abstract loadInstance(pk: PKT): Promise<T>;

    /**
     * An overridable method for loading any data, beyond the instance.
     *
     * @see {@linkcode loadInstance}
     * @abstract
     * @returns A promise that resolves when the data has been loaded.
     */
    protected async load?(): Promise<void>;

    public override connectedCallback(): void {
        super.connectedCallback();

        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.#instancePk) return;

            this.loadInstance(this.#instancePk).then((instance) => {
                this.instance = instance;
            });
        });
    }

    public override async firstUpdated(): Promise<void> {
        if (this.#instancePk && !this.#initialLoad) {
            this.instancePk = this.#instancePk;
            this.#initialLoad = true;
        } else if (!this.#initialDataLoad) {
            // else if since if the above case triggered that will also call this.load(), so
            // ensure we don't load again
            this.load?.().then(() => {
                this.#initialDataLoad = true;
                // Class attributes changed in this.load() might not be @property()
                // or @state() so let's trigger a re-render to be sure we get updated
                this.requestUpdate();
            });
        }
    }

    //#endregion

    //#region Public methods

    public override reset(): void {
        this.instance = this.createDefaultInstance?.() ?? null;
        this.#initialLoad = false;
    }

    //#endregion

    //#region Rendering

    protected override render(): SlottedTemplateResult {
        if ((this.#instancePk && !this.instance) || !this.#initialDataLoad) {
            return html`<ak-empty-state loading></ak-empty-state>`;
        }

        return super.render();
    }

    //#endregion
}
