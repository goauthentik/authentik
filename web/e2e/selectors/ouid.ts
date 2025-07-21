/* eslint-disable no-console */

type SelectorRoot = Document | ShadowRoot;

export function createOUIDNameEngine() {
    const attributeName = "data-ouid-component-name";

    console.log("Creating OUID selector engine!!");
    return {
        // Returns all elements matching given selector in the root's subtree.
        queryAll(scope: SelectorRoot, componentName: string) {
            const result: Element[] = [];

            const match = (element: Element) => {
                const name = element.getAttribute(attributeName);

                if (name === componentName) {
                    result.push(element);
                }
            };

            const query = (root: Element | ShadowRoot | Document) => {
                const shadows: ShadowRoot[] = [];

                if ((root as Element).shadowRoot) {
                    shadows.push((root as Element).shadowRoot!);
                }

                for (const element of root.querySelectorAll("*")) {
                    match(element);

                    if (element.shadowRoot) {
                        shadows.push(element.shadowRoot);
                    }
                }

                shadows.forEach(query);
            };

            query(scope);
            return result;
        },
    };
}
