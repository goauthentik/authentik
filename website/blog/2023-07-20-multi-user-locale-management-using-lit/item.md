---
title: "Multi-user locale management using Lit"
slug: 2023-07-20-multi-user-locale-management-using-lit
authors:
    - name: Kenneth Sternberg
      title: Sr. Frontend Developer at Authentik Security Inc
      url: https://github.com/kensternberg-authentik
      image_url: https://github.com/kensternberg-authentik.png
tags:
    - blog
    - lit
    - multi-user
    - translation
    - locale
    - authentik
hide_table_of_contents: false
image: ./image1.jpg
---

[Lit](https://lit.dev/) comes with its own library to help your app support multiple written languages. Lit's localization feature updates the page automatically when a language is switched during a browser session, but the documentation does not describe **how** you can switch languages.

Let's dive into how you might do that.

![](./image1.jpg)

<!--truncate-->

## Lit and Localization

Lit is a library from Google that enables the construction of fast, reactive web applications by leveraging the browser's own component model and event handling rather than imposing it from the outside as React, Angular, and other application development platforms do. Lit's [Web Components](https://modern-web.dev/) are fast, efficient, reactive, and comply with the [actual standards](https://developer.mozilla.org/en-US/docs/Web/API/Web_components) for how browsers should behave as application platforms.

Lit's only failing is that the standards came late and actual standardization on that behavior across Chrome, Firefox, Safari, and Edge didn't complete until early 2020. By that time React had been out for seven years and had a massive share of the market.

Lit has an effective [localization library](https://lit.dev/docs/localization/overview/) that supports both a static and a dynamic mode. Most developers I've spoken with prefer the dynamic mode, because it affords the user the option of changing languages without having to reload the page. We will use that mode.

## Basics of Lit Localize

The basics of Lit's localization workflow are as follows:

-   Build your app, wrapping every text string you'll want the user to see in a `msg("Your text here")` function wrapper.
-   Specify a `lit-localize.json` file, specifying the language you use as the source locale, and providing a list of target locales you want your application to support.
-   Run `lit-localize extract`, which will extract all the `msg()` blocks and update your catalog of locale files, one separate file per target locale. If you've done this before, any already translated strings will not be discarded or overwritten.
-   Send your locale files to your translators. When you get a translated file back, replace the existing file with it.
-   Run `lit-localize build`, which will then build the translation files (in JavaScript or Typescript, depending on your project settings) that the `msg()` blocks will then display in the user's language (if it's available).

When your web application starts up, the top-level context must run the library's `configureLocalization()` function, which takes three arguments: the source language's [locale code](https://www.loc.gov/standards/iso639-2/php/code_list.php), the list of available target languages, and a function that asynchronously loads the locale file for the specified target. It returns two functions, `getLocale()` and `setLocale(localeCode: string)`.

Now, any Lit web component in your application with the `@localized()` decorator will update immediately and automatically with a new language.

## Managing the Locale context

But what if we want to update the language dynamically? What if your customer enters your site and then specifies that they want, say, French instead of English? The Lit Localize library doesn't cover that, so let's do that ourselves.

Let's create a [Lit context](https://lit.dev/docs/data/context/). That's straightforward enough:

```typescript
// ./localize/context.ts
import { createContext } from "@lit-labs/context";
export const localeContext = createContext<string>("locale");
export default localeContext;
```

All we're storing in this is the string for the locale. There are any number of places where the locale request could come from: the user's browser setting, the URL, a configuration setting from the server, the default fallback. Once we have the context and the `configureLocalization()`function, we need to preserve and update that context. Here's what the top of that context object looks like:

```typescript
@customElement("locale-context")
export class LocaleContext extends LitElement {
    @provide({ context: locale })
    @property()
    locale = "en";
    constructor() {
        super();
        const [getLocale, setLocale] = configureLocalization();
        this.getLocale = getLocale;
        this.setLocale = setLocale;
        this.updateLocaleHandler = this.updateLocaleHandler.bind(this);
    }
    connectedCallback() {
        super.connectedCallback();
        window.addEventListener('custom-request-locale-change', this.updateLocaleHandler);
        this.setLocale(this.locale);
    }
    disconnectedCallback() {
        window.removeEventListener('custom-request-locale-change', this.updateLocaleHandler);
        super.connectedCallback();
    }
    updateLocaleHandler(ev: Event) {
        this.updateLocale((ev as CustomEvent).detail.locale);
        ev.stopPropagation();
    }
    render() {
        return html`<slot></slot>`;
    }

```

This is fairly boiler-plate. When this components is constructed by the browser it loads the locale and sets up the update handler. Because the update handler runs in the context of an event handler, we make sure to `.bind()` it to the instance that it will need to access. When this component is connected to the browser, it will have access to the requested locale specified when it becomes part of the DOM, so we call `setLocale()` at that moment.

The `as CustomEvent` cast there is just for show; please do something smarter with an [assertion function](https://blog.logrocket.com/assertion-functions-typescript/).

The only oddity is at the top: `@provide({ context: locale })` comes from Lit's context library. It turns the object field associated with it into a context manager, and any child objects contained within this context will get **that** value, and no other, if they import and examine the context object. Attach a `@consume({ context: yourcontext })` decorator to a `@property` or `@state` field, and any Lit component will react to the change of context no matter how far up the tree it is with a re-render.

And finally, we don't actually want to do anything visually interesting with our context, we just want to supply the data and manage it, so our application returns an empty `<slot></slot>` object into which we put the rest of our application. Slots are rendered in the context of the [LightDOM](https://lit-element.readthedocs.io/en/v0.6.4/docs/templates/slots/), so any of your content wrapped in our `<locale-context locale="fr"><your-content></your-content></locale-context>` will have access to the full browser environment.

A few things are **not** specified in this example; if you want this object to be able to go through that list above of sources-of-truth for the current locale on startup rather than use the `@property` string, you'll need more code in the `connectedCallback` that what I've done there.

The reason we preserve `getLocale()` and `setLocale()` here is that Lit Localize's library is a singleton; if you run `configureLocalization` twice in the same browser session it throws an exception. So we make sure to run it once and preserve its localizing powers.

With all that in mind, the actual `updateLocale` library is easy:

```typescript
    updateLocale(code: string) {
        if (this.getLocale() === code) {
            return;
        }
        const locale = getBestMatchLocale(code);
        if (!locale) {
            console.warn(`failed to find locale for code ${code}`);
            return;
        }
        this.setLocale(locale)
    }
```

I won't provide the function `getBestMatchLocale`; it takes the requested locale code you pass it and returns an object containing the path to the locale file, the exact code you want to instantiate, and a label for the language such as "French" or "English" or "Chinese (Traditional)".

It uses a prioritized table of regular expressions so that, for example, a request for `fr_FR` will be mapped to the `fr.ts` language file.

Remember that **you** supply the loader function to `configureLocalization()`, so it can take anything you want; I chose for it to take that object. If the file is not already present when you call `setLocale()`, it loads it. When that file is available, it then issues a message causing all Lit Web Components on the page decorated with the `@localize()` class decorator to request a re-render with the new language strings.

## Changing the Locale Context

This is the easiest part. I mentioned that `getBestMatchLocale` has a table with the code, a regex matcher, the human-readable label for the language, and the import instructions; you can now use that table to create a `<select>` box anywhere in your application with the label for text and the locale code for a value.

When the user makes a selection, your component just needs to send an event:

```javascript
this.dispatchEvent(
    new CustomEvent("custom-request-locale-change", {
        composed: true,
        bubbles: true,
        details: { locale: requestedCode },
    }),
);
```

...and that's it. The top-level context will receive this event and attempt to load the requested locale. If that works, it will fire off a re-render request and all your text will be updated with the new language pack.

## What We've Done

We've described and implemented a context manager that associates your Lit Web Component user and application settings with Lit's own localization library. We have provided an event listener to that context manager so that changes to the locale string will dynamically update your Lit application's displayed text in the language requested. Under the classic rule of "A class should have only one reason to do its thing, and it should do its thing well," this fits the bill: that one reason is "the locale **string** changed." We've seen how to apply localization to all our own components via the `@localized()` decorator, and we've described how we might display the list of locales and shown how a locale change request is sent to the context manager.

You now have the tools you need to provide your Lit application to customers around the world in their own language. May you find a million new customers who don't speak your language!
