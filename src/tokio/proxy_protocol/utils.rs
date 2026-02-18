use std::{
    net::{IpAddr, Ipv4Addr, Ipv6Addr},
    str::FromStr,
};

pub(super) fn read_until(buf: &[u8], delim: u8) -> Option<&[u8]> {
    for i in 0..buf.len() {
        if buf[i] == delim {
            return Some(&buf[..i]);
        }
    }
    None
}

pub(super) trait AddressFamily: FromStr + Into<IpAddr> {
    const BYTES: usize;

    fn from_slice(slice: &[u8]) -> Self;
}

impl AddressFamily for Ipv4Addr {
    const BYTES: usize = (Self::BITS / 8) as usize;

    fn from_slice(slice: &[u8]) -> Self {
        let arr: [u8; Self::BYTES] = slice.try_into().expect("slice must be 4 bytes");
        arr.into()
    }
}

impl AddressFamily for Ipv6Addr {
    const BYTES: usize = (Self::BITS / 8) as usize;

    fn from_slice(slice: &[u8]) -> Self {
        let arr: [u8; Self::BYTES] = slice.try_into().expect("slice must be 16 bytes");
        arr.into()
    }
}
