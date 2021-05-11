import { property } from "lit-element";
import { EVENT_REFRESH } from "../../constants";
import { Form } from "./Form";

export abstract class ModelForm<T, PKT extends string | number> extends Form<T> {

    abstract loadInstance(pk: PKT): Promise<T>;

    @property({attribute: false})
    set instancePk(value: PKT) {
        this._instancePk = value;
        this.loadInstance(value).then(instance => {
            this.instance = instance;
        });
    }

    private _instancePk?: PKT;

    @property({ attribute: false })
    instance?: T = this.defaultInstance;

    get defaultInstance(): T | undefined {
        return undefined;
    }

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this._instancePk) return;
            this.loadInstance(this._instancePk).then(instance => {
                this.instance = instance;
            });
        });
    }

}
