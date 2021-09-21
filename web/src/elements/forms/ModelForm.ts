import { TemplateResult } from "lit";
import { property } from "lit/decorators";
import { EVENT_REFRESH } from "../../constants";
import { Form } from "./Form";

export abstract class ModelForm<T, PKT extends string | number> extends Form<T> {
    viewportCheck = true;

    abstract loadInstance(pk: PKT): Promise<T>;

    @property({ attribute: false })
    set instancePk(value: PKT) {
        this._instancePk = value;
        if (this.viewportCheck && !this.isInViewport) {
            return;
        }
        this.loadInstance(value).then((instance) => {
            this.instance = instance;
            this.requestUpdate();
        });
    }

    private _instancePk?: PKT;

    private _initialLoad = false;

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

    render(): TemplateResult {
        // if we're in viewport now and haven't loaded AND have a PK set, load now
        if (this.isInViewport && !this._initialLoad && this._instancePk) {
            this.instancePk = this._instancePk;
            this._initialLoad = true;
        }
        return super.render();
    }
}
