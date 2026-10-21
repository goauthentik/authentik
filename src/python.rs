//! The Python interpreter embedded in this process.

use std::path::PathBuf;

use eyre::Result;
use pyo3::{prelude::*, types::PyDict};

/// Start the interpreter and make authentik and the packages of its virtualenv importable.
///
/// The interpreter is linked into this binary instead of being started from the virtualenv,
/// so it doesn't find the virtualenv on its own.
pub(crate) fn initialize() -> Result<()> {
    Python::initialize();
    let venv =
        std::env::var_os("VIRTUAL_ENV").map_or_else(|| PathBuf::from(".venv"), PathBuf::from);
    let venv = std::path::absolute(venv)?;
    let cwd = std::env::current_dir()?;
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
        let sys = py.import("sys")?;
        // For anything that starts Python itself, like multiprocessing
        sys.setattr("executable", venv.join("bin").join("python").as_os_str())?;
        // `python -m` puts the working directory first, so that `authentik` can be imported
        let path = sys.getattr("path")?;
        if !path.contains(cwd.as_os_str())? {
            path.call_method1("insert", (0_i32, cwd.as_os_str()))?;
        }
        Ok::<_, PyErr>(())
    })?;
    Ok(())
}
