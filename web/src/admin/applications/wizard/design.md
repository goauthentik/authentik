The design of the wizard is actually very simple. There is an orchestrator in the Context object;
it takes messages from the current page and grants permissions to proceed based on the content of
the Context object after a message.

The fields of the Context object are:

```Javascript
{
   step: number // The page currently being visited
   providerType: The provider type chosen in step 2. Dictates which view to show in step 3
   application: // The data collected from the ApplicationDetails page
   provider: // the data collected from the ProviderDetails page.


```

The orchestrator leans on the per-page forms to tell it when a page is "valid enough to proceed".

When it reaches the last page, the transaction is triggered. If there are errors, the user is
invited to "go back to the page where the error occurred" and try again.
