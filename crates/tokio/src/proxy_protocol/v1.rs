use std::{
    net::{Ipv4Addr, Ipv6Addr, SocketAddr},
    str::{FromStr, from_utf8},
};

use super::header::{Error, Header};
use crate::proxy_protocol::{
    header::{Address, Protocol},
    utils::{AddressFamily, read_until},
};

const MAX_LENGTH: usize = 107;
const GREETING: &[u8] = b"PROXY";
const UNKNOWN: &[u8] = b"PROXY UNKNOWN\r\n";
// All other valid PROXY headers are longer than this
const MIN_LENGTH: usize = UNKNOWN.len();

fn parse_addr<A: AddressFamily>(buf: &[u8], pos: &mut usize) -> Result<A, Error> {
    let Some(address) = read_until(&buf[*pos..], b' ') else {
        return Err(Error::BufferTooShort);
    };

    let addr = from_utf8(address)
        .map_err(|_| Error::Invalid)
        .and_then(|s| A::from_str(s).map_err(|_| Error::Invalid))?;
    *pos += address.len() + 1;

    Ok(addr)
}

fn parse_port(buf: &[u8], pos: &mut usize, delim: u8) -> Result<u16, Error> {
    let Some(port) = read_until(&buf[*pos..], delim) else {
        return Err(Error::BufferTooShort);
    };

    let p = from_utf8(port)
        .map_err(|_| Error::Invalid)
        .and_then(|s| u16::from_str(s).map_err(|_| Error::Invalid))?;
    *pos += port.len() + 1;

    Ok(p)
}

fn parse_addrs<A: AddressFamily>(buf: &[u8], pos: &mut usize) -> Result<Address, Error> {
    let src_addr: A = parse_addr(buf, pos)?;
    let dst_addr: A = parse_addr(buf, pos)?;
    let src_port = parse_port(buf, pos, b' ')?;
    let dst_port = parse_port(buf, pos, b'\r')?;

    Ok(Address {
        protocol: Protocol::Stream, // v1 only supports TCP
        source: SocketAddr::new(src_addr.into(), src_port),
        destination: SocketAddr::new(dst_addr.into(), dst_port),
    })
}

fn decode_inner(buf: &[u8]) -> Result<(Header<'_>, usize), Error> {
    let mut pos = 0;

    if buf.len() < MIN_LENGTH {
        return Err(Error::BufferTooShort);
    }
    if !buf.starts_with(GREETING) {
        return Err(Error::Invalid);
    }
    pos += GREETING.len() + 1;

    let addrs = if buf[pos..].starts_with(b"UNKNOWN") {
        let Some(rest) = read_until(&buf[pos..], b'\r') else {
            return Err(Error::BufferTooShort);
        };
        pos += rest.len() + 1;

        None
    } else {
        let proto = &buf[pos..pos + 5];
        pos += 5;

        match proto {
            b"TCP4 " => Some(parse_addrs::<Ipv4Addr>(buf, &mut pos)?),
            b"TCP6 " => Some(parse_addrs::<Ipv6Addr>(buf, &mut pos)?),
            _ => return Err(Error::Invalid),
        }
    };

    match buf.get(pos) {
        Some(b'\n') => pos += 1,
        None => return Err(Error::BufferTooShort),
        _ => return Err(Error::Invalid),
    }

    Ok((Header(addrs, Default::default()), pos))
}

/// Decode a version 1 PROXY header from a buffer.
///
/// Returns the decoded header and the number of bytes consumed from the buffer.
pub(super) fn decode(buf: &[u8]) -> Result<(Header<'_>, usize), Error> {
    // Guard against a malicious client sending a very long header, since it is a
    // delimited protocol.
    match decode_inner(buf) {
        Err(Error::BufferTooShort) if buf.len() >= MAX_LENGTH => Err(Error::Invalid),
        other => other,
    }
}
