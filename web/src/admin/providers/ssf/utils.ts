import { DeliveryMethodEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";

export function SSFDeliveryMethodToLabel(method?: DeliveryMethodEnum): string {
    if (!method) return "";
    switch (method) {
        case DeliveryMethodEnum.HttpsSchemasOpenidNetSeceventRiscDeliveryMethodPoll:
        case DeliveryMethodEnum.UrnIetfRfc8936:
            return msg("Pull");
        case DeliveryMethodEnum.HttpsSchemasOpenidNetSeceventRiscDeliveryMethodPush:
        case DeliveryMethodEnum.UrnIetfRfc8935:
            return msg("Push");
    }
    return "";
}
