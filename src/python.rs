//! The Python interpreter embedded in this process.

use std::path::PathBuf;

use eyre::Result;
use pyo3::{prelude::*, types::PyDict};

/// Start the interpreter and make the packages of authentik's virtualenv importable.
///
/// The interpreter is linked into this binary instead of being started from the virtualenv,
/// so it doesn't find the virtualenv on its own.
pub(crate) fn initialize() -> Result<()> {
    Python::initialize();
    let venv =
        std::env::var_os("VIRTUAL_ENV").map_or_else(|| PathBuf::from(".venv"), PathBuf::from);
    let venv = std::path::absolute(venv)?;
    Python::attach(|py| {
        let vars = PyDict::new(py);
        vars.set_item("base", venv.as_os_str())?;
        vars.set_item("platbase", venv.as_os_str())?;
        let sysconfig = py.import("sysconfig")?;
        let site = py.import("site")?;
        for name in ["purelib", "platlib"] {
            let kwargs = PyDict::new(py);
            kwargs.set_item("scheme", "venv")?;
            kwargs.set_item("vars", &vars)?;
            let path = sysconfig.call_method("get_path", (name,), Some(&kwargs))?;
            // Also handles the `.pth` files of editable installs
            site.call_method1("addsitedir", (path,))?;
        }
        // For anything that starts Python itself, like multiprocessing
        py.import("sys")?
            .setattr("executable", venv.join("bin").join("python").as_os_str())?;
        Ok::<_, PyErr>(())
    })?;
    Ok(())
}
