import { EVENT_REFRESH } from "@goauthentik/common/constants";
import "@goauthentik/elements/EmptyState";
import { Form } from "@goauthentik/elements/forms/Form";

import { TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

/**
 * Model form
 *
 * A base form that automatically tracks the server-side object (instance)
 * that we're interested in.  Handles loading and tracking of the instance.
 */

export abstract class ModelForm<T, PKT extends string | number> extends Form<T> {
    abstract loadInstance(pk: PKT): Promise<T>;

    async load(): Promise<void> {
        return Promise.resolve();
    }

    @property({ attribute: false })
    set instancePk(value: PKT) {
        this._instancePk = value;
        if (this.viewportCheck && !this.isInViewport) {
            return;
        }
        if (this._isLoading) {
            return;
        }
        this._isLoading = true;
        this.load().then(() => {
            this.loadInstance(value).then((instance) => {
                this.instance = instance;
                this._isLoading = false;
                this.requestUpdate();
            });
        });
    }

    private _instancePk?: PKT;

    // Keep track if we've loaded the model instance
    private _initialLoad = false;
    // Keep track if we've done the general data loading of load()
    private _initialDataLoad = false;

    private _isLoading = false;

    @property({ attribute: false })
    instance?: T = this.defaultInstance;

    get defaultInstance(): T | undefined {
        return undefined;
    }

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this._instancePk) return;
            this.loadInstance(this._instancePk).then((instance) => {
                this.instance = instance;
            });
        });
    }

    resetForm(): void {
        this.instance = undefined;
        this._initialLoad = false;
    }

    renderVisible(): TemplateResult {
        if ((this._instancePk && !this.instance) || !this._initialDataLoad) {
            return html`<ak-empty-state ?loading=${true}></ak-empty-state>`;
        }
        return super.renderVisible();
    }

    render(): TemplateResult {
        // if we're in viewport now and haven't loaded AND have a PK set, load now
        // Or if we don't check for viewport in some cases
        const viewportVisible = this.isInViewport || !this.viewportCheck;
        if (this._instancePk && !this._initialLoad && viewportVisible) {
            this.instancePk = this._instancePk;
            this._initialLoad = true;
        } else if (!this._initialDataLoad && viewportVisible) {
            // else if since if the above case triggered that will also call this.load(), so
            // ensure we don't load again
            this.load().then(() => {
                this._initialDataLoad = true;
                // Class attributes changed in this.load() might not be @property()
                // or @state() so let's trigger a re-render to be sure we get updated
                this.requestUpdate();
            });
        }
        return super.render();
    }
}
