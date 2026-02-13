export type TelegramUserResponse = {
    id: number;
    first_name?: string;
    last_name?: string;
    username?: string;
    photo_url?: string;
    auth_date: number;
    hash: string;
};

export function loadTelegramWidget(
    targetElement: Element | undefined,
    botUsername: string,
    requestMessageAccess: boolean,
    callback: (user: TelegramUserResponse) => void,
) {
    const widgetScript = document.createElement("script");
    widgetScript.src = "https://telegram.org/js/telegram-widget.js?22";
    widgetScript.type = "text/javascript";
    widgetScript.setAttribute("data-radius", "0");
    widgetScript.setAttribute("data-telegram-login", botUsername);
    if (requestMessageAccess) {
        widgetScript.setAttribute("data-request-access", "write");
    }
    const callbackName =
        "__ak_telegram_login_callback_" + (Math.random() + 1).toString(36).substring(7);
    (window as unknown as Record<string, (user: TelegramUserResponse) => void>)[callbackName] =
        callback;
    widgetScript.setAttribute("data-onauth", callbackName + "(user)");
    targetElement?.appendChild(widgetScript);
    widgetScript.onload = () => {
        if (widgetScript.previousSibling) {
            targetElement?.appendChild(widgetScript.previousSibling);
        }
    };
    document.body.append(widgetScript);
}
