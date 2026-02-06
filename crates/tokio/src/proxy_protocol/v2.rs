use std::{
    borrow::Cow,
    net::{Ipv4Addr, Ipv6Addr, SocketAddr},
};

use super::header::{Error, Header};
use crate::proxy_protocol::{
    header::{Address, Protocol},
    utils::AddressFamily,
};

const GREETING: &[u8] = b"\r\n\r\n\x00\r\nQUIT\n";
const MIN_LENGTH: usize = GREETING.len() + 4;
const AF_UNIX_ADDRS_LEN: usize = 216;

fn parse_addrs<T: AddressFamily>(
    buf: &[u8],
    pos: &mut usize,
    rest: &mut usize,
    protocol: Protocol,
) -> Result<Address, Error> {
    if buf.len() < *pos + T::BYTES * 2 + 4 {
        return Err(Error::BufferTooShort);
    }
    if *rest < T::BYTES * 2 + 4 {
        return Err(Error::Invalid);
    }

    let addr = Address {
        protocol,
        source: SocketAddr::new(
            T::from_slice(&buf[*pos..*pos + T::BYTES]).into(),
            u16::from_be_bytes([buf[*pos + T::BYTES * 2], buf[*pos + T::BYTES * 2 + 1]]),
        ),
        destination: SocketAddr::new(
            T::from_slice(&buf[*pos + T::BYTES..*pos + T::BYTES * 2]).into(),
            u16::from_be_bytes([buf[*pos + T::BYTES * 2 + 2], buf[*pos + T::BYTES * 2 + 3]]),
        ),
    };

    *rest -= T::BYTES * 2 + 4;
    *pos += T::BYTES * 2 + 4;

    Ok(addr)
}

/// Decode a version 2 PROXY header from a buffer.
///
/// Returns the decoded header and the number of bytes consumed from the buffer.
pub(super) fn decode(buf: &[u8]) -> Result<(Header<'_>, usize), Error> {
    let mut pos = 0;

    if buf.len() < MIN_LENGTH {
        return Err(Error::BufferTooShort);
    }
    if !buf.starts_with(GREETING) {
        return Err(Error::Invalid);
    }
    pos += GREETING.len();

    let is_local = match buf[pos] {
        0x20 => true,
        0x21 => false,
        _ => return Err(Error::Invalid),
    };
    let protocol = buf[pos + 1];
    let mut rest = u16::from_be_bytes([buf[pos + 2], buf[pos + 3]]) as usize;
    pos += 4;

    if buf.len() < pos + rest {
        return Err(Error::BufferTooShort);
    }

    let addr_info = match protocol {
        0x00 => None,
        0x11 => Some(parse_addrs::<Ipv4Addr>(
            buf,
            &mut pos,
            &mut rest,
            Protocol::Stream,
        )?),
        0x12 => Some(parse_addrs::<Ipv4Addr>(
            buf,
            &mut pos,
            &mut rest,
            Protocol::Datagram,
        )?),
        0x21 => Some(parse_addrs::<Ipv6Addr>(
            buf,
            &mut pos,
            &mut rest,
            Protocol::Stream,
        )?),
        0x22 => Some(parse_addrs::<Ipv6Addr>(
            buf,
            &mut pos,
            &mut rest,
            Protocol::Datagram,
        )?),
        0x31 | 0x32 => {
            // AF_UNIX - we don't parse it, but don't reject it either in case we need the TLVs
            if rest < AF_UNIX_ADDRS_LEN {
                return Err(Error::Invalid);
            }
            rest -= AF_UNIX_ADDRS_LEN;
            pos += AF_UNIX_ADDRS_LEN;
            None
        }
        _ => return Err(Error::Invalid),
    };

    let tlv_data = Cow::Borrowed(&buf[pos..pos + rest]);

    pos += rest;

    let header = if is_local {
        Header(None, tlv_data)
    } else {
        Header(addr_info, tlv_data)
    };

    Ok((header, pos))
}
