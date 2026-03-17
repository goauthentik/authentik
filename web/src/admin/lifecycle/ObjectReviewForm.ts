import "#components/ak-textarea-input";
import "#elements/forms/ModalForm";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";

import { LifecycleApi, LifecycleIteration, Review } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-object-review-form")
export class ObjectReviewForm extends ModelForm<Review, string> {
    @property({ attribute: false })
    public iteration: LifecycleIteration | null = null;

    protected loadInstance(_pk: string): Promise<Review> {
        throw new TypeError("Reviews should not be edited.");
    }

    protected send(data: Review): Promise<unknown> {
        return new LifecycleApi(DEFAULT_CONFIG).lifecycleReviewsCreate({
            reviewRequest: data,
        });
    }

    protected override serialize(): Review | null {
        const review = super.serialize();

        if (!review || !this.iteration) return null;

        review.iteration = this.iteration.id;

        return review;
    }

    renderForm(): TemplateResult {
        return html`<ak-textarea-input
            label=${msg("Review Notes")}
            placeholder=${msg("Type optional notes to include in this review...")}
            name="note"
        ></ak-textarea-input>`;
    }
}
