function convertToSlug(Text) {
    return Text
        .toLowerCase()
        .replace(/[^\w ]+/g, '')
        .replace(/ +/g, '-')
        ;
}


const $source = $('input[name=name]');
const $result = $('input[name=slug]');

const typeHandler = function (e) {
    $result.val(convertToSlug(e.target.value));
}

$source.on('input', typeHandler) // register for oninput
$source.on('propertychange', typeHandler) // for IE8
