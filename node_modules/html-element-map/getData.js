'use strict';

var callBound = require('call-bind/callBound');

var $push = callBound('Array.prototype.push');

var map = function (arr, mapper) {
	var mapped = [];
	for (var i = 0; i < arr.length; i += 1) {
		$push(mapped, mapper(arr[i], i));
	}
	return mapped;
};

var expecteds = [
	['HTMLElement', 'article'],
	['HTMLElement', 'section'],
	['HTMLBaseFontElement', 'basefont', 'HTMLBaseFontElementConstructor'], // Safari 5.1
	['HTMLPhraseElement', 'cite', 'HTMLElement'], // Safari 5.1
	['HTMLElement', 'noscript'],
	['HTMLBGSoundElement', 'bgsound', 'HTMLElement'], // Safari 5.1
	['HTMLPhraseElement', 'blink', 'HTMLElement'], // Safari 5.1
	['HTMLElement', 'multicol'],
	['HTMLNextIdElement', 'nextid', 'HTMLElement'], // Safari 5.1
	['HTMLElement', 'rb'],
	['HTMLElement', 'spacer'],
	['HTMLAnchorElement', 'a', 'HTMLElement'], // Safari 5.1
	// ['HTMLAppletElement', 'applet'], // commented out due to IE 11 java update popup
	['HTMLAreaElement', 'area', 'HTMLElement'], // Safari 5.1
	['HTMLAudioElement', 'audio', 'HTMLElement'], // Safari 5.1
	['HTMLBaseElement', 'base', 'HTMLElement'], // Safari 5.1
	['HTMLBodyElement', 'body', 'HTMLElement'], // Safari 5.1
	['HTMLBRElement', 'br', 'HTMLElement'], // Safari 5.1
	['HTMLButtonElement', 'button'],
	['HTMLCanvasElement', 'canvas'],
	['HTMLContentElement', 'content', 'HTMLElement'], // Safari 5.1
	['HTMLDataElement', 'data', 'HTMLElement'], // Safari 5.1
	['HTMLDataListElement', 'datalist'],
	['HTMLDialogElement', 'dialog', 'HTMLElement'], // Safari 5.1
	['HTMLDirectoryElement', 'dir'],
	['HTMLDivElement', 'div'],
	['HTMLDListElement', 'dl'],
	['HTMLEmbedElement', 'embed'],
	['HTMLFieldSetElement', 'fieldset'],
	['HTMLFontElement', 'font'],
	['HTMLFormElement', 'form'],
	['HTMLFrameElement', 'frame'],
	['HTMLFrameSetElement', 'frameset'],
	['HTMLHeadElement', 'head'],
	['HTMLHeadingElement', 'h1'],
	['HTMLHeadingElement', 'h2'],
	['HTMLHeadingElement', 'h3'],
	['HTMLHeadingElement', 'h4'],
	['HTMLHeadingElement', 'h5'],
	['HTMLHeadingElement', 'h6'],
	['HTMLHtmlElement', 'html'],
	['HTMLHRElement', 'hr'],
	['HTMLIFrameElement', 'iframe'],
	['HTMLImageElement', 'img'],
	['HTMLInputElement', 'input'],
	['HTMLIsIndexElement', 'index', 'HTMLElement'], // in HTML5, this is HTMLUnknownElement (Safari 5.1 for HTMLElement)
	['HTMLKeygenElement', 'keygen', 'HTMLBlockElement'],
	['HTMLLabelElement', 'label'],
	['HTMLLegendElement', 'legend'],
	['HTMLLIElement', 'li'],
	['HTMLLinkElement', 'link'],
	['HTMLElement', 'main'], // in IE 9-11, this is HTMLUnknownElement
	['HTMLMapElement', 'map'],
	['HTMLMarqueeElement', 'marquee'],
	['HTMLMenuElement', 'menu'],
	['HTMLMetaElement', 'meta'],
	['HTMLMeterElement', 'meter', 'HTMLElement'], // Safari 5.1
	['HTMLModElement', 'del'],
	['HTMLModElement', 'ins'],
	['HTMLObjectElement', 'object'],
	['HTMLOListElement', 'ol'],
	['HTMLOptGroupElement', 'optgroup'],
	['HTMLOptionElement', 'option'],
	['HTMLOutputElement', 'output'],
	['HTMLParagraphElement', 'p'],
	['HTMLParamElement', 'param'],
	['HTMLPictureElement', 'picture', 'HTMLElement'], // Safari 5.1
	['HTMLPreElement', 'pre'],
	['HTMLProgressElement', 'progress', 'HTMLElement'], // Safari 5.1
	['HTMLQuoteElement', 'q', 'HTMLBlockquoteElement'], // Safari 5.1
	['HTMLQuoteElement', 'blockquote', 'HTMLBlockElement', 'HTMLBlockquoteElement'], // Safari 5.1
	['HTMLScriptElement', 'script'],
	['HTMLSelectElement', 'select'],
	['HTMLShadowElement', 'shadow', 'HTMLElement'], // Safari 5.1
	['HTMLSourceElement', 'source'],
	['HTMLSpanElement', 'span', 'HTMLElement'], // Safari 5.1
	['HTMLStyleElement', 'style'],
	['HTMLTableElement', 'table'],
	['HTMLTableCaptionElement', 'caption'],
	['HTMLTableCellElement', 'td', 'HTMLTableDataCellElement'],
	['HTMLTableCellElement', 'th', 'HTMLTableHeaderCellElement'],
	['HTMLTableRowElement', 'tr'],
	['HTMLTableColElement', 'col'],
	['HTMLTableColElement', 'colgroup'],
	['HTMLTableSectionElement', 'tbody'],
	['HTMLTableSectionElement', 'thead'],
	['HTMLTableSectionElement', 'tfoot'],
	['HTMLTemplateElement', 'template', 'HTMLElement'], // Safari 5.1
	['HTMLTextAreaElement', 'textarea'],
	['HTMLTimeElement', 'time', 'HTMLElement'], // Safari 5.1
	['HTMLTitleElement', 'title'],
	['HTMLTrackElement', 'track', 'HTMLElement'], // Safari 5.1
	['HTMLUListElement', 'ul'],
	['HTMLVideoElement', 'video'],
	['HTMLElement', 'abbr'],
	['HTMLElement', 'address'],
	['HTMLElement', 'aside'],
	['HTMLElement', 'b'],
	['HTMLElement', 'bdi'],
	['HTMLElement', 'bdo'],
	['HTMLElement', 'code'],
	['HTMLElement', 'dd'],
	['HTMLDetailsElement', 'details', 'HTMLElement'], // Safari 5.1
	['HTMLElement', 'dfn'],
	['HTMLElement', 'dt'],
	['HTMLElement', 'em'],
	['HTMLElement', 'figcaption'],
	['HTMLElement', 'figure'],
	['HTMLElement', 'footer'],
	['HTMLElement', 'header'],
	['HTMLElement', 'hgroup'],
	['HTMLElement', 'i'],
	['HTMLElement', 'kbd'],
	['HTMLElement', 'mark'],
	['HTMLElement', 'nav'],
	['HTMLElement', 'rp'],
	['HTMLElement', 'rt'],
	['HTMLElement', 'ruby'],
	['HTMLElement', 's'],
	['HTMLElement', 'samp'],
	['HTMLSlotElement', 'slot', 'HTMLElement'], // Safari 5.1
	['HTMLElement', 'small'],
	['HTMLElement', 'strong'],
	['HTMLElement', 'summary'],
	['HTMLElement', 'u'],
	['HTMLElement', 'var'],
	['HTMLElement', 'wbr']
];

// eslint-disable-next-line consistent-return, max-params
var getConstructor = function getTagConstructor(tag, constructor, unknown) {
	if (typeof document !== 'undefined' && typeof document.createElement === 'function') {
		var actual = document.createElement(tag).constructor;
		if (actual !== unknown) {
			return actual;
		}
	}
};

module.exports = function getData() {
	var unknown = global.HTMLUnknownElement;
	return {
		all: global.HTMLElement,
		elements: map(expecteds, function (expected) {
			var constructorName = expected[0];
			var tag = expected[1];
			var alternate;
			var altConstructor;
			for (var i = 2; i < arguments.length && !altConstructor; i += 1) {
				alternate = expected[i];
				altConstructor = alternate && global[alternate];
			}
			var constructor = global[constructorName];

			return {
				constructor: getConstructor(tag, altConstructor || constructor, unknown),
				constructorName: altConstructor ? alternate : constructorName,
				expectedConstructor: altConstructor || constructor,
				tag: tag
			};
		}),
		unknown: unknown
	};
};
