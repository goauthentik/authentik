//! Decoding for messages of the PostgreSQL channel layer.
//!
//! Python serializes every message with `MessagePack` and compresses it with zlib, see
//! `PostgresChannelLayerLoopProxy.serialize` in
//! `packages/django-channels-postgres/django_channels_postgres/layer.py`.

use std::io::Read as _;

use eyre::{Result, eyre};
use flate2::read::ZlibDecoder;
use rmpv::Value as MsgpackValue;
use serde_json::{Map, Number, Value};

/// Largest decompressed message we accept. Channels documents 1 MB as the message size limit.
const MAX_MESSAGE_SIZE: u64 = 1024 * 1024;

/// Decodes a message the way `PostgresChannelLayerLoopProxy.deserialize` does.
///
/// Messages are always dictionaries, so the result is a JSON object.
pub(super) fn decode(data: &[u8]) -> Result<Map<String, Value>> {
    let mut decompressed = Vec::new();
    ZlibDecoder::new(data)
        .take(MAX_MESSAGE_SIZE + 1)
        .read_to_end(&mut decompressed)?;
    if u64::try_from(decompressed.len())? > MAX_MESSAGE_SIZE {
        return Err(eyre!(
            "channel layer message exceeds {MAX_MESSAGE_SIZE} bytes"
        ));
    }
    let value = rmpv::decode::read_value(&mut decompressed.as_slice())?;
    match to_json(value)? {
        Value::Object(map) => Ok(map),
        _ => Err(eyre!("channel layer message is not a map")),
    }
}

/// Converts a `MessagePack` value to JSON, as `json.dumps` would serialize the Python value.
fn to_json(value: MsgpackValue) -> Result<Value> {
    Ok(match value {
        MsgpackValue::Nil => Value::Null,
        MsgpackValue::Boolean(value) => Value::Bool(value),
        MsgpackValue::Integer(value) => {
            if let Some(value) = value.as_u64() {
                Value::from(value)
            } else if let Some(value) = value.as_i64() {
                Value::from(value)
            } else {
                return Err(eyre!("integer {value} is out of range"));
            }
        }
        MsgpackValue::F32(value) => float(f64::from(value)),
        MsgpackValue::F64(value) => float(value),
        MsgpackValue::String(value) => Value::String(
            value
                .into_str()
                .ok_or_else(|| eyre!("string is not valid UTF-8"))?,
        ),
        MsgpackValue::Array(items) => {
            Value::Array(items.into_iter().map(to_json).collect::<Result<_>>()?)
        }
        MsgpackValue::Map(entries) => {
            let mut map = Map::with_capacity(entries.len());
            for (key, value) in entries {
                // `json.dumps` turns integer keys into strings, and rejects other kinds.
                let key = match key {
                    MsgpackValue::String(key) => key
                        .into_str()
                        .ok_or_else(|| eyre!("map key is not valid UTF-8"))?,
                    MsgpackValue::Integer(key) => key.to_string(),
                    other => return Err(eyre!("unsupported map key {other}")),
                };
                map.insert(key, to_json(value)?);
            }
            Value::Object(map)
        }
        MsgpackValue::Binary(_) | MsgpackValue::Ext(..) => {
            return Err(eyre!("binary values can't be represented as JSON"));
        }
    })
}

/// JSON has no NaN or infinity. Python would write them as invalid JSON, we write `null`.
fn float(value: f64) -> Value {
    Number::from_f64(value).map_or(Value::Null, Value::Number)
}

#[cfg(test)]
pub(super) mod tests {
    use std::io::Write as _;

    use flate2::{Compression, write::ZlibEncoder};
    use serde_json::json;

    use super::*;

    /// A notification message as `NotificationTransport.send_local` sends it, serialized by the
    /// Python channel layer. `authentik/root/tests/test_websocket_internal.py` checks that
    /// Python still produces the same bytes for the same message.
    pub(in super::super) const PYTHON_NOTIFICATION: &[u8] =
        include_bytes!("testdata/notification.msgpack.zlib");

    pub(in super::super) fn python_notification() -> Value {
        json!({
            "type": "event.notification",
            "id": "5ba8d8bc-5d36-4a17-9bba-e1b8c3d6a0b4",
            "data": {
                "pk": "5ba8d8bc-5d36-4a17-9bba-e1b8c3d6a0b4",
                "severity": "notice",
                "body": "Ünïcödé body",
                "created": "2026-11-12T10:00:00.000000Z",
                "event": null,
                "seen": false,
                "hyperlink": null,
                "hyperlink_label": null,
                "count": 3,
                "ratio": 0.5,
                "tags": ["a", "b"],
            },
        })
    }

    /// Serializes `value` the way the Python channel layer does.
    pub(in super::super) fn encode(value: &MsgpackValue) -> Vec<u8> {
        let mut msgpack = Vec::new();
        rmpv::encode::write_value(&mut msgpack, value).expect("failed to encode");
        let mut encoder = ZlibEncoder::new(Vec::new(), Compression::new(6));
        encoder.write_all(&msgpack).expect("failed to compress");
        encoder.finish().expect("failed to compress")
    }

    #[test]
    fn decodes_python_message() {
        let decoded = decode(PYTHON_NOTIFICATION).expect("failed to decode");
        assert_eq!(Value::Object(decoded), python_notification());
    }

    #[test]
    fn integer_keys_become_strings() {
        let value = MsgpackValue::Map(vec![(MsgpackValue::from(1_i32), MsgpackValue::from("one"))]);
        let decoded = decode(&encode(&value)).expect("failed to decode");
        assert_eq!(Value::Object(decoded), json!({"1": "one"}));
    }

    #[test]
    fn rejects_binary_values() {
        let value = MsgpackValue::Map(vec![(
            MsgpackValue::from("bytes_data"),
            MsgpackValue::Binary(vec![0, 1, 2]),
        )]);
        let err = decode(&encode(&value)).expect_err("binary values must be rejected");
        assert!(err.to_string().contains("binary"), "{err}");
    }

    #[test]
    fn rejects_non_map_messages() {
        let err = decode(&encode(&MsgpackValue::from("not a map"))).expect_err("must be rejected");
        assert!(err.to_string().contains("not a map"), "{err}");
    }

    #[test]
    fn rejects_data_that_is_not_zlib() {
        let _err = decode(b"definitely not zlib").expect_err("must be rejected");
    }

    #[test]
    fn rejects_oversized_messages() {
        let size = usize::try_from(MAX_MESSAGE_SIZE).expect("fits") + 1;
        let value = MsgpackValue::Map(vec![(
            MsgpackValue::from("body"),
            MsgpackValue::from("a".repeat(size)),
        )]);
        let err = decode(&encode(&value)).expect_err("oversized messages must be rejected");
        assert!(err.to_string().contains("exceeds"), "{err}");
    }
}
