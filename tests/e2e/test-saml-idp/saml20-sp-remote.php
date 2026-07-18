<?php
/**
 * SAML 2.0 remote SP metadata for SimpleSAMLphp.
 *
 * See: https://simplesamlphp.org/docs/stable/simplesamlphp-reference-sp-remote
 */

$metadata[getenv('SIMPLESAMLPHP_SP_ENTITY_ID')] = array(
    'AssertionConsumerService' => getenv('SIMPLESAMLPHP_SP_ASSERTION_CONSUMER_SERVICE'),
    'SingleLogoutService' => getenv('SIMPLESAMLPHP_SP_SINGLE_LOGOUT_SERVICE'),
);

if (null != getenv('SIMPLESAMLPHP_SP_NAME_ID_FORMAT')) {
    $metadata[getenv('SIMPLESAMLPHP_SP_ENTITY_ID')] = array_merge($metadata[getenv('SIMPLESAMLPHP_SP_ENTITY_ID')], array('NameIDFormat' => getenv('SIMPLESAMLPHP_SP_NAME_ID_FORMAT')));
}

if (null != getenv('SIMPLESAMLPHP_SP_NAME_ID_ATTRIBUTE')) {
    $metadata[getenv('SIMPLESAMLPHP_SP_ENTITY_ID')] = array_merge($metadata[getenv('SIMPLESAMLPHP_SP_ENTITY_ID')], array('simplesaml.nameidattribute' => getenv('SIMPLESAMLPHP_SP_NAME_ID_ATTRIBUTE')));
}

if (null != getenv('SIMPLESAMLPHP_SP_SIGN_ASSERTION')) {
    $metadata[getenv('SIMPLESAMLPHP_SP_ENTITY_ID')] = array_merge($metadata[getenv('SIMPLESAMLPHP_SP_ENTITY_ID')], array('saml20.sign.assertion' => ('true' == getenv('SIMPLESAMLPHP_SP_SIGN_ASSERTION'))));
}
