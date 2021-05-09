import { property } from "lit-element";
import { EVENT_REFRESH } from "../../constants";
import { Form } from "./Form";

export abstract class ModelForm<T, PKT> extends Form<T> {

    abstract loadInstance(pk: PKT): Promise<T>;

    @property()
    set instancePk(value: PKT) {
        this._instancePk = value;
        this.loadInstance(value).then(instance => {
            this.instance = instance;
        });
    }

    private _instancePk?: PKT;

    @property({ attribute: false })
    instance?: T;

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
