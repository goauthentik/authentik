---
title: “We “had an authentic Hackathon!
slug: 2023-08-02-we-had-an-authentik-hackathon
authors:
   - name: Tana Berry
      title: Sr. Technical Content Editor at Authentik Security Inc
      url: https://github.com/tanberry
      image_url: https://github.com/tanberry.png
tags:
    - blog
    - hackathon
    - docathon
    - team work
    - code
    - authentik
    - git
    - identity management
    - authentication
hide_table_of_contents: false
image: ./image1.jpg
---

<aside>
🎉 Congratulations to all participants and to the Top Three prize winners!

</aside>

The first ever authentik hackathon just wrapped on Sunday, and we had a great time!

A huge thanks to our persistent hackers, who hacked from Wednesday through Sunday, and made some fantastic contributions to [authentik](https://goauthentik.io/). We are already looking forward to the next one (winter 2023, maybe?), and to another round of intense fun with our community members.

![](./image1.jpg)

<!--truncate-->

### Our intrepid participants

We had folks spread across four continents and six continents! From the US West coast (Pacific timezone) to Texas to Western Africa, Central Europe, Eastern Europe and Mumbai, India, we had a time difference spread of 12 and a half hours. So yes, timezones are, errrrmmm… interesting. But it was actually quite manageable, and thanks to those on the early and late extremes of the hours! While not all of the people who registered actually showed up and hacked with us, those who participated were energized and very ready to contribute to and learn about authentik.

Over the five days, we stayed in touch with each other using voice chat on our #hackathon channel in Discord, during regularly scheduled Check-in calls. Throughout the day we could check in with each other on team-specific channels or on the main #hackathon channel.

### What we hacked on

Take a look at our [GitHub repo](https://github.com/goauthentik/authentik) for specific Issues and PRs, but the contributions ranged widely, from email configurations to define allow-lists (thanks @sandeep2244!), to adding Kerberos as an authentication protocol (kudos to @mareo and @risson for this amazing and challenging contribution!), to a wonderfully surprising amount of documentation additions, testing and improvements (way to win, @Baloc and @richardokonicha!!)!

![emial_lists.png](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/9b37144d-fdec-4d0c-a71e-174e05bc39cd/emial_lists.png)

![dog-ring.jpg](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/d0324ab6-da74-458f-9f58-1d4ef6af9fe4/dog-ring.jpg)

![icon_docs.png](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/1167f708-337a-4839-b128-0556e4017001/icon_docs.png)

We also had PRs to improve the authentik UI (specifically the Library page of applications), and a detailed, in-depth answer to a question about how to prompt users, via authentik’s customizable Flows and Policies and also by using incentivization, to configure a multi-factor authentication tool (thank you @smileyj!).

### And the top three winners are…

![three-awards.jpeg](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/17a4dd00-2f0f-4095-beea-4f4afe0a9da3/three-awards.jpeg)

Congrats to the top prize winners:

- Our contributor @richardokonicha from Nigeria took third place for his hard work on our Beta upgrade docs.. which led to improvements on additional docs for the  Docker Compose and the Kubernetes installation documentation. Richard will be forever famous for his insistence on testing the documentation (Every. Step. Of. It.) and for putting on the user’s hat in order to produce clear, simple instructions.
- The Wow Factor Contribution of adding Kerberos as a new authentication protocol came in at second place, and was worked on at a furious pace by two fellow Frenchmen, @mareo and @risson. Dramatic demos and happy tired faces are *de riguer* at hackathons, and this substantial contribution did not disappoint!
- At top place is @Baloc, who also hails from France, and added substantial value by contributing procedural docs abut user management. The tech docs badly need more How To content, and @Baloc bravely dove right in. We now have shiny new docs for all of the CRUD operations plus a load of reference content about session details, events, tokens, group memberships, MFA authenticators… there’s a lot of powerful functionality in authentik’s user management, and now we have docs to prove it!

### Oh the [good] drama!

Working closely with others on a project, sharing screens back and forth, with a relatively tight timeline can add a level of excitement and energy. Maybe we were lucky and just happened to have the World’s Nicest People as our participants, or maybe software folk are just like that, but the energy was always positive and there were always helping hands (and eyes) available if things got sticky.

### Highlights

Some of the best takeaways form the event include:

- Watching others work is fascinating…. we all have our own ways of moving around our IDEs, making quick edits to config files (vi anyone?) and navigating Git repos, but wow the variety of exactly how different people do the same task is amazing. Learning from others is going to happen for sure at a hackathon, and surprisingly you can even learn a bit about yourself and your work patterns!
- Embrace the rabbit holes! Sure, it can be exhausting for us introverts to interact with people and learn a TON from watching their work styles, and even more exhausting when you realize that your hacking partner is correct, we really *DO* need to install a K8S cluster so that you can do some testing… but it is also immensely rewarding. A hackathon is the perfect time to give yourself permission to try something new, to spend a long while banging at something, guilt-free, and to put your real-world work responsibilities aside.
- The strength of community, and the ever-fresh wonder of chatting with people for all over the globe. Everyone in software is a builder, and building with others, in cities or locales that you might never have even heard of, is simply amazing, refreshing, and fun.
- authentik does a lot more than even our (relatively new) authentik team knew! (Well, our founder and CTO Jens knew, since he built it…) It was great fun to explore some of the deeper capabilities and functionality of authentik, and to have the original builder there to learn from.
- We had fun and moved fast, but also pushed our discipline to follow the regular authentik  build rules (like `make website`) , naming standards for our PRs, coding guidelines, etc. A little standardization and rule-following didn’t dampen any of the fun, and made things easier when it was time to create PRs and merge our contributions.

### Join us for the next one!

We aren’t yet sure of the exact schedule, but authentik will definitely have another Hackathon! We will have more great prizes (we know money isn’t everything but a little competitive compensation for your time and effort is nice!), and celebrate the camaraderie and contributions.

In the meantime, drop into our repo anytime, look around, and see if there is anything to want to hack on and make a contribution!

See you there, and thank you all for being part of the authentik community.
