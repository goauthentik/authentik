---
title: "Let’s make identity fun again (whether we build it or buy it)"
slug: 2023-08-16-lets-make-identity-fun-again
authors:
    - name: Jens Langhammer
      title: CTO at Authentik Security Inc
      url: https://github.com/BeryJu
      image_url: https://github.com/BeryJu.png
tags:
    - build-vs-buy
    - SSO
    - third-party software
    - identity provider
    - vendors
    - security
    - authentication
hide_table_of_contents: false
image: ./image1.jpg
---

Identity – whether we’re talking about internal authentication (think Auth0) or external authentication (think Okta) – has become boring.

Little else proves this better than the fact that Okta and Auth0 are now the same company and that their primary competitor, Microsoft AD, survives based on [bundling and momentum](https://goauthentik.io/blog/2023-07-07-Microsoft-has-a-monopoly-on-identity). Identity has become a commodity – a component you buy off the shelf, integrate, and ignore.

Of course, taking valuable things for granted isn’t always bad. We might regularly drive on roads we don’t think much about, for example, but that doesn’t make them any less valuable.

The danger with letting identity become boring is that we’re not engaging in the problem and we’re letting defaults drive the conversation rather than context-specific needs. We’re not engaging in the solution because we’re not encouraging a true buy vs. build discussion.

> My pitch: Let’s make identity fun again. And in doing so, let’s think through a better way to decide whether to build or buy software.

[![Image1](./image1.jpg)](https://pixabay.com/users/jplenio-7645255/ "Image by jplenio on pixabay")

<!--truncate-->

## How identity became boring and the big players became defaults

There are one million articles about build vs. buy because it’s one of those problems that won’t go away. Ironically, despite the never-ending discussion, there tends to be a firm anchor: build the features that differentiate your product and build everything else.

Jeff Lawson, co-founder and CEO of Twilio captured this well in his book _Ask Your Developer_, writing that “My rule of thumb is that for anything that gives you differentiation with customers, you should build. Software that faces your customers, you should build.”

Within this framework, identity almost inevitably appears to be the perfect example of buying instead of building. When has a login screen ever made one product stand out from another? When has a user ever said, “The product is good but the authentication process brought me joy”?

It’s easy, obvious, and – from within this framework – correct to buy your identity feature. Identity isn’t unique here but the strength of the consensus around buying instead of building is striking.

Small startups, on one end of the spectrum, tend to strictly follow the rule of thumb above. Along the way to product/market fit, and often well after it, startups find it worthwhile to invest almost everything into the bleeding edge features that will wedge them into the market.

Identity is an early requirement they often want to sweep away. Identity becomes a commodity to buy and the defaults – usually Okta and Auth0 – feel obvious.

Enterprises, on the other end of the spectrum, tend to be swamped with bureaucracy and overwhelmed by internal and external demands. Enterprises tend to need extensive feature coverage, multitudes of integrations, and always-on customer support. From this perspective, defaults appear attractive and Microsoft AD becomes compelling.

> Across the spectrum, identity has developed the reputation of being a boring problem with a commodity solution.

If companies were aware of the tradeoffs that come from choosing the default path, we wouldn’t be having this conversation. But for many companies, the default feels like a standard, and all the non-standard paths are obscured.

## Build vs. buy and its extremes

The “build your core; buy everything else” framework feels authoritative because its logic is built on logic we don’t do a good job of questioning.

Is there actually always great software to buy? Is build vs. buy a black-and-white decision? Do we actually have a good understanding of differentiation?

No, no, and also no.

### Third-party software is a market for lemons

Lawson’s rule of thumb implicitly relies on an idea in economics called the [efficient-market hypothesis](https://en.wikipedia.org/wiki/Efficient-market_hypothesis). The basic idea is this: assets and asset prices reflect all available information.

There are decades of economists arguing back and forth on the accuracy of this idea, that all data points are brought to the table. But in a cultural and business context, it’s been honed into a simple assumption: the market incentivizes identifying and solving problems and over time, for the most part, the best possible solution is available at any given time.

But there’s a competing theory that explains the software procurement process better: the [market for lemons](https://en.wikipedia.org/wiki/The_Market_for_Lemons) concept. The core argument is that in a market with information asymmetry between buyers and sellers, the quality of the products can degrade and buyers can end up with defective products (lemons).

Third-party software procurement is often surprisingly inefficient and when you think about your actual experiences purchasing software or using purchased software, you’ll likely remember a lot of lemons (even if few software vendors are actually like a used car salesperson).

Dan Luu has a great article on the topic called [Why is it so hard to buy things that work well?](https://danluu.com/nothing-works/) He writes that companies, in principle, should be able to outsource work outside their core competencies but that those who do, in his experience, “have been very unhappy with the results compared to what they can get by hiring dedicated engineers.”

This disappointment applies in absolute terms (meaning the product might not be as good as promised or that support isn’t efficient at making it work for you) and in financial terms (meaning large contracts can often end up costing more than the salaries of the engineers you otherwise would have hired).

Examples abound, including a product that was supposed to sync data from Postgres to Snowflake that ultimately lost data, duplicated data, and corrupted data. There’s also Cloudflare Access, [named by Wave’s then-CTO Ben Kuhn](https://twitter.com/benskuhn/status/1382325921311563779?s=20), that came with a product-breaking login problem that the Cloudflare support team misinterpreted before escalating to an engineering team, who “declared it working as intended.”

The market doesn’t need to exclusively comprise lemons to be a market of lemons; the information asymmetry just needs to be imbalanced enough, consistently enough, that the typical buy vs. build framework doesn’t work.

The primary benefit of the API economy, in theory, was the rise of hyper-specialized services built by hyper-specialized engineers.

But there’s a downside: If no one knows more about payment processing than Stripe, then how can other engineers adequately evaluate the options? And that doesn’t just apply to sheer functionality. In-house engineers are likely going to struggle to evaluate the quality of the integrations and the amount of support necessary and available too.

Consensus provides little relief. As Dan writes, “Even after selecting the consensus best product in the space from the leading (as in largest and most respected) firm, and using the main offering the company has, the product often not only doesn't work but, by design, can't work.”

## Buy vs. build as a false dichotomy

The build vs. buy framework often fails because the “vs.” implies a black-and-white comparison between building software from scratch and buying vendor software that’s effectively a black box.

Once you decide you only need a commodity feature, you start to treat the feature as a solved problem that’s solved by an efficient market. And once you assume that, the consensus default becomes the obvious choice.

There are two misconceptions buried in the false dichotomy:

-   To _build instead of buy_ is to build from scratch.
-   To _buy instead of build_ is to get a complete solution in one package.

In the first misconception, we tend to treat the process of building software as building from the ground up. Building tends to get associated with wastefulness or over-indulgence. This is a shallow way to think about this option, however, considering how many ways you can adopt open source components, buy component parts you can build with and adapt, or build on extensible tools and platforms.

And when you purchase component parts from smaller vendors instead of buying “complete” packages from large vendors, you often get to work more closely with the vendor and shape the product in a way that works for you (and for other customers like you). A vendor option can then be customizable out-of-the-box and customizable long-term as you work alongside the vendor.

> Customization of the log in and authentication workflow, using our editable flows, stages, and UI elements, is a core out-of-the-box feature of [authentik](https://goauthentik.io/).

In the second misconception, we tend to assume that the offered solution is complete and that buying a product merely involves breaking out the company credit card. That might be what the vendors pitch but more often than not, there are significant costs to maintenance and integration. Duncan Greenberg, Vice President at Oscar Health, has [argued](https://medium.com/oscar-tech/the-many-pitfalls-of-build-vs-buy-5364f49a4fed) that “The choice is also often better seen as buy and maintain or buy and integrate” because, he writes, “Some amount of building is always required.”

And while some of these costs can be written off as short-term, others linger. Will Larson, CTO at Carta, [writes that risks include](https://lethain.com/build-vs-buy/) “the vendor going out of business, shifting their pricing in a way that’s incompatible with your usage, suffering a severe security breach that makes you decide to stop working with them, or canceling the business line.”

Even open-source and open-core components can pose this danger. Consider HashiCorp’s recent [controversial licensing change](https://twitter.com/HashiCorp/status/1689733106813562880?s=20).

### Differentiation is not always obvious

Finally, one of the most misleading aspects of the typical buy vs. build framework is how it leans on an idea that’s hard to define: differentiation.

In the original framework, startups are supposed to build only the features that differentiate their products from other products or that otherwise make them stand out and feel valuable to their target customers.

There’s a compelling logic to this because it often makes sense to devote most of your resources to a single opportunity instead of spreading yourself thin. When you start to achieve product/market fit, the market “[pulls product out of the startup](<https://a16z.com/2017/02/18/12-things-about-product-market-fit-2/#:~:text=The%20question%20then%20is%3A%20who,organically%20(i.e.%2C%20without%20any%20advertising)>).” And when that happens, it makes sense to work in that direction rather than distracting yourself with other tasks.

The trouble is that the directive to build customer-facing features isn’t always a good framework. Netflix, for example, built the whole idea of chaos engineering because they couldn’t buy the kind of resilience they needed. Customers would benefit but most wouldn’t even notice; still, they built.

This is another way the efficient market hypothesis can lead us astray.

Sometimes, even industry-leading vendors aren’t a good fit. They might be missing features you need; they might charge exorbitant prices for your usage levels or for essential features like SSO; and they might not be iterating fast enough to keep up with changing demands.

The more carefully you think not only about _what_ differentiates you but _how_ you can make [X feature] into something that differentiates you, the more you’ll find reasons to build.

## Security is 90% execution and 10% innovation

One of the best reasons to buy software is because a vendor is naturally incentivized to iterate, innovate, and keep up with a changing market (a market that likely isn’t yours but may feed into yours).

It would be obviously foolish, for example, to try building your own LLM instead of working with OpenAI. They’re already far ahead and they’ve built a machine for staying ahead and going faster.

This dynamic, however, isn’t true across many markets. Unlike AI, where most of the market feels like whitespace, modern security concerns are fairly well mapped out. There are many issues, of course, and many gaps in the market remain, but there aren’t many paradigm shifts on the horizon nor problem areas that still require pioneers.

> We’re not doing brain surgery, in other words; we’re matching prescriptions to known diagnoses.

In security, where the typical build vs. buy framework perhaps works the least well, security teams can turn into pilots and drivers of tools instead of engineers. Adrian Sanabria, Director of Product Marketing at Valence Security, [explains that many security teams](https://medium.com/@sawaba/when-to-purchase-a-solution-to-your-cybersecurity-problem-86de1fa203ba) have “mistaken a bill of goods for a security program.” In the process, he writes, there become “entire security ‘teams’ that are little more than babysitters for a particular product the company owns.”

And this is where the opportunity to build (or customize) instead of buy exists. In a mature industry, where standards are stable and most problems have at least broad solutions, it often makes more sense to build a feature in-house so that you can execute it as well as possible.

There comes a point where the creation and implementation remaining to be done is best done by the people closest to the precise problem in its exact context. In the security industry, success depends more on a granular understanding of the problem than sheer innovation.

## Let’s make identity fun again

We can make identity – as well as many similar problems – fun again. We can resist defaulting to industry leaders and insist on building custom solutions or building on top of products that will grow with us.

The goal isn’t to flip our defaults and start building everything from scratch. The goal is to reexamine our building and buying criteria and recontextualize them in our industries, use cases, and particular needs. The more we do so, the more we’ll find that building is a better path than we might have guessed.

And even if building isn’t the right option, reconsidering our choices and our decision criteria will help us figure out how to search for better vendors and how to fully evaluate them.

For years, we’ve tried to avoid building as much as possible and it’s an extreme that is worth resisting or at least questioning. But as someone who’s building around identity every day, I can assure you it’s more fun than you’d guess and more rewarding – both for you and your users.
