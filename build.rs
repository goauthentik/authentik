fn main() {
    #[cfg(feature = "core")]
    {
        pyo3_build_config::add_libpython_rpath_link_args();
    }
}
