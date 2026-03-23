import "#elements/EmptyState";

import { AKRefreshEvent } from "#common/events";

import { listen } from "#elements/decorators/listen";
import { Form } from "#elements/forms/Form";
import { asInvoker } from "#elements/modals/utils";
import { SlottedTemplateResult } from "#elements/types";

import { ConsoleLogger } from "#logger/browser";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { property } from "lit/decorators.js";

export interface ModelFormConstructor {
    instancePk: string | number;
    new (): ModelForm;
}

/**
 * A base form that automatically tracks the server-side object (instance)
 * that we're interested in. Handles loading and tracking of the instance.
 *
 * @template T The type of the model instance.
 * @template PKT The type of the primary key of the model instance.
 * @template D The result of `toJSON()`, which is the data sent to the server on submit.
 *
 * @prop {T} instance - The current instance being edited or viewed.
 * @prop {PKT} instancePk - The primary key of the instance to load.
 */
export abstract class ModelForm<
    T extends object = object,
    PKT extends string | number = string | number,
    D = T,
> extends Form<T, D> {
    /**
     * A helper method to create an invoker for editing an instance of this form.
     *
     * The invoker will look for a `data-pk` attribute on the clicked element to determine which instance to load.
     *
     * ```ts
     * class AKUserListPage extends TablePage<User> {
     *   #openEditUserModal = UserForm.asEditModalInvoker();
     * }
     *```
     *
     * @see {@linkcode Form.asModalInvoker} for opening a blank form in a modal.
     * @see {@linkcode asInvoker} for the underlying implementation.
     */
    public static asEditModalInvoker() {
        return asInvoker((event) => {
            const instancePk = (event.currentTarget as HTMLElement).dataset.pk;

            if (!instancePk && typeof instancePk !== "number") {
                console.error("No pk found on event target:", event);
                throw new TypeError("No pk found on event target.");
            }

            const FormConstructor = this as unknown as ModelFormConstructor;
            const formElement = new FormConstructor();
            formElement.instancePk = instancePk;

            return formElement;
        });
    }

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

    protected override formatSubmitLabel(): string {
        if (this.#instancePk) {
            return msg(str`Save Changes`, {
                id: "model-form.apply-submit",
            });
        }

        return this.entitySingular
            ? msg(str`Create ${this.entitySingular}`, {
                  id: "model-form.create-submit",
              })
            : msg("Create", {
                  id: "model-form.create-submit-no-entity",
              });
    }

    protected override formatHeadline(): string {
        const verb = this.#instancePk ? msg("Edit") : msg("New");
        const noun = this.entitySingular;

        if (!noun) return verb;

        return msg(str`${verb} ${noun}`, {
            id: "model-form.headline",
            desc: "The headline for a form that creates or updates a model instance.",
        });
    }

    //#region Public methods

    public override reset(): void {
        super.reset();

        this.instance = undefined;
        this.#initialLoad = false;
        this.#initialDataLoad = false;

        this.requestUpdate();
    }

    //#endregion

    //#region Rendering

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

    //#endregion
}
