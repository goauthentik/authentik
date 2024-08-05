import { slug } from "github-slugger";

import { html, render } from "lit";

import "../ak-search-select-view.js";
import { groupedSampleData, sampleData } from "../stories/sampleData.js";
import { AkSearchSelectViewDriver } from "./ak-search-select-view.comp.js";

const longGoodForYouPairs = {
    grouped: false,
    options: sampleData.map(({ produce }) => [slug(produce), produce]),
};

describe("Search select: Test Input Field", () => {
    let select: AkSearchSelectViewDriver;

    beforeEach(async () => {
        await render(
            html`<ak-search-select-view .options=${longGoodForYouPairs} blankable>
            </ak-search-select-view>`,
            document.body,
        );
        select = await AkSearchSelectViewDriver.build(await $("ak-search-select-view"));
    });

    it("should open the menu when the input is clicked", async () => {
        expect(await select.inputState()).toBe(0);
        await select.clickInput();
        expect(await select.inputState()).toBe(2);
    });

    it("should open the menu when the input is focused", async () => {
        expect(await select.inputState()).toBe(0);
        await select.focusOnInput();
        expect(await select.inputState()).toBe(2);
    });

    it("should open the menu when the input is clicked a second time", async () => {
        expect(await select.inputState()).toBe(0);
        expect(await select.menuIsVisible()).toBe(false);
        await select.clickInput();
        expect(await select.menuIsVisible()).toBe(true);
        expect(await select.inputState()).toBe(2);
    });

    it("should close the menu when the user clicks away", async () => {
        document.body.insertAdjacentHTML(
            "afterbegin",
            '<input id="a-separate-component" type="text" />',
        );
        const input = await $("#a-separate-component");

        await select.clickInput();
        expect(await select.inputState()).toBe(2);
        input.click();
        expect(await select.inputState()).toBe(0);
    });

    it("should reopen the menu when the input is clicked", async () => {});

    afterEach(async () => {
        await document.body.querySelector("#a-separate-component")?.remove();
        await document.body.querySelector("ak-search-select-view").remove();
        document.body["_$litPart$"] && delete document.body["_$litPart$"];
    });
});

describe("Search Select: Empty Options", () => {
    let select: AkSearchSelectViewDriver;

    beforeEach(async () => {
        await render(
            html`<ak-search-select-view .options=${[]} blankable> </ak-search-select-view>`,
            document.body,
        );
        select = await AkSearchSelectViewDriver.build(await $("ak-search-select-view"));
    });

    it("should not show the menu if there are no options", async () => {
        expect(await select.inputState()).toBe(0);
        expect(await select.menuIsVisible()).toBe(false);
        await select.clickInput();
        expect(await select.inputState()).toBe(1);
        expect(await select.menuIsVisible()).toBe(false);
    });

    afterEach(async () => {
        await document.body.querySelector("#a-separate-component")?.remove();
        await document.body.querySelector("ak-search-select-view").remove();
        document.body["_$litPart$"] && delete document.body["_$litPart$"];
    });
});

//    should toggle the visibility when typing and closing the panel (API layer)

//    should provide the open state of the panel

//  should not close the panel when clicking on the input
//  should not close the panel when clicking on the input inside shadow DOM
//  should have the correct text direction in RTL
//  should update the panel direction if it changes for the trigger
//  should be able to set a custom value for the `autocomplete` attribute
//  should not throw when typing in an element with a null and disabled autocomplete
//  should clear the selected option if it no longer matches the input text while typing
//  should not clear the selected option if it no longer matches the input text while typing with requireSelection
//    should update control value as user types with input value
//    should update control value when autofilling
//    should update control value when option is selected with option value
//    should update the control back to a string if user types after an option is selected
//    should fill the text field with display value when an option is selected
//    should fill the text field with value if displayWith is not set
//    should fill the text field correctly if value is set to obj programmatically
//    should clear the text field if value is reset programmatically
//    should clear the previous selection when reactive form field is reset programmatically
//    should disable input in view when disabled programmatically
//    should mark the autocomplete control as dirty as user types
//    should mark the autocomplete control as dirty when an option is selected
//    should not mark the control dirty when the value is set programmatically
//    should mark the autocomplete control as touched on blur
//    should disable the input when used with a value accessor and without `matInput`
//    should transfer the theme to the autocomplete panel
//    should not focus the option when DOWN key is pressed
//    should not close the panel when DOWN key is pressed
//    should set the active item to the first option when DOWN key is pressed
//    should set the active item to the last option when UP key is pressed
//    should set the active item properly after filtering
//    should set the active item properly after filtering
//    should fill the text field when an option is selected with ENTER
//    should prevent the default enter key action
//    should not prevent the default enter action for a closed panel after a user action
//    should not interfere with the ENTER key when pressing a modifier
//    should fill the text field, not select an option, when SPACE is entered
//    should mark the control dirty when selecting an option from the keyboard
//    should open the panel again when typing after making a selection
//    should not open the panel if the `input` event was dispatched with changing the value
//    should scroll to active options below the fold
//    should scroll to active options below if the option height is variable
//    should scroll to active options on UP arrow
//    should not scroll to active options that are fully in the panel
//    should scroll to active options that are above the panel
//    should close the panel when pressing escape
//    should prevent the default action when pressing escape
//    should not close the panel when pressing escape with a modifier
//    should close the panel when pressing ALT + UP_ARROW
//    should close the panel when tabbing away from a trigger without results
//    should not close when a click event occurs on the outside while the panel has focus
//    should reset the active option when closing with the escape key
//    should reset the active option when closing by selecting with enter
//    should not prevent the default action when a modifier key is pressed
//    should scroll to active options below the fold
//    should scroll to active options on UP arrow
//    should scroll to active options that are above the panel
//    should scroll back to the top when reaching the first option with preceding group label
//    should scroll to active option when group is indirect descendant
//    should set role of input to combobox
//    should set role of autocomplete panel to listbox
//    should point the aria-labelledby of the panel to the field label
//    should add a custom aria-labelledby to the panel
//    should trim aria-labelledby if the input does not have a label
//    should clear aria-labelledby from the panel if an aria-label is set
//    should clear aria-labelledby if the form field does not have a label
//    should support setting a custom aria-label
//    should set aria-autocomplete to list
//    should set aria-activedescendant based on the active option
//    should set aria-expanded based on whether the panel is open
//    should set aria-expanded properly when the panel is hidden
//    should set aria-controls based on the attached autocomplete
//    should not set aria-controls while the autocomplete is closed
//    should restore focus to the input when clicking to select a value
//    should remove autocomplete-specific aria attributes when autocomplete is disabled
//    should use below positioning by default
//    should reposition the panel on scroll
//    should fall back to above position if panel cannot fit below
//    should allow the panel to expand when the number of results increases
//    should align panel properly when filtering in "above" position
//     it(
//    should not throw if a panel reposition is requested while the panel is closed
//    should be able to force below position even if there is not enough space
//    should be able to force above position even if there is not enough space
//    should handle the position being changed after the first open
//    should deselect any other selected option
//    should call deselect only on the previous selected option
//    should be able to preselect the first option
//    should not activate any option if all options are disabled
//    should remove aria-activedescendant when panel is closed with autoActiveFirstOption
//    should be able to preselect the first option when the floating label is disabled
//    should be able to configure preselecting the first option globally
//    should handle `optionSelections` being accessed too early
//    should emit to `optionSelections` if the list of options changes
//    should reposition the panel when the amount of options changes
//    should clear the selected option when the input value is cleared
//    should accept the user selection if they click on an option while selection is required
//    should accept the user selection if they press enter on an option while selection is required
//    should accept the user selection if autoSelectActiveOption is enabled
//    should clear the value if selection is required and the user interacted with the panel without selecting anything
//    should preserve the value if a selection is required, but the user opened and closed the panel without interacting with it
//    should preserve the value if a selection is required, and there are no options
//    should clear the value if requireSelection is enabled and the user edits the input before clicking away
//    should emit panel close event when clicking away
//    should emit panel close event when tabbing out
//    should not emit when tabbing away from a closed panel
//    should emit panel close event when selecting an option
//    should close the panel when pressing escape
//    should not throw when clicking outside
//    should apply them if provided as string
//    should apply them if provided as array
//    should allow basic use without any forms directives
//    should display an empty input when the value is undefined with ngModel
//    should display the number when the selected option is the number zero
//    should work when input is wrapped in ngIf
//    should filter properly with ngIf after setting the active item
//    should throw if the user attempts to open the panel too early
//    should not throw on init, even if the panel is not defined
//    should transfer the mat-autocomplete classes to the panel element
//    should remove old classes when the panel class changes
//    should reset correctly when closed programmatically
//    should handle autocomplete being attached to number inputs
//    should not focus the option when DOWN key is pressed
//    should revert back to the last typed value if the user presses escape
//    should emit a closed event if no option is displayed
//    should propagate the auto-selected value if the user clicks away
//    should propagate the auto-selected value if the user tabs away
//    should propagate the auto-selected value if the user presses enter on it
//    should allow the user to click on an option different from the auto-selected one
//  should have correct width when opened
//  should update the width while the panel is open
//  should not reopen a closed autocomplete when returning to a blurred tab
//  should update the panel width if the window is resized
//  should have panel width match host width by default
//  should have panel width set to string value
//  should have panel width set to number value
//  should emit an event when an option is selected
//  should refocus the input after the selection event is emitted
//  should emit an event when a newly-added option is selected
//  should emit an event when an option is activated
//  should not emit the optionActivated event when the active option is reset
//  should be able to set a custom panel connection element
//  should be able to change the origin after the panel has been opened
//  should be able to re-type the same value when it is reset while open
//  should not close when clicking inside alternate origin
//    should display checkmark for selection by default
//    should not display checkmark
//    should add the id of the autocomplete panel to the aria-owns of the modal
//    should remove the aria-owns attribute of the modal when the autocomplete panel closes
//    should re-add the aria-owns attribute of the modal when the autocomplete panel opens again
