"""Docker SSH helper tests"""

from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from authentik.outposts.docker_ssh import FOOTER, HEADER, DockerInlineSSH


def block(host: str, key_path: str) -> str:
    """Config block as DockerInlineSSH.write_config writes it"""
    return (
        f"{HEADER} - {host}\n"
        f"Host {host}\n"
        f"    IdentityFile {key_path}\n"
        "    StrictHostKeyChecking No\n"
        "    UserKnownHostsFile /dev/null\n"
        f"{FOOTER}\n"
        "\n"
    )


class DockerInlineSSHCleanupTests(SimpleTestCase):
    """DockerInlineSSH.cleanup tests"""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = Path(self.tmp.name, "config")
        self.key = Path(self.tmp.name, "key.pem")
        self.key.write_text("key", encoding="utf-8")
        self.ssh = DockerInlineSSH.__new__(DockerInlineSSH)
        self.ssh.host = "a.example"
        self.ssh.header = f"{HEADER} - a.example\n"
        self.ssh.config_path = self.config
        self.ssh.key_path = str(self.key)

    def test_block_at_top(self):
        """A block at the start of the file is removed completely"""
        other = block("b.example", "/tmp/b.pem")
        self.config.write_text(block("a.example", str(self.key)) + other, encoding="utf-8")
        self.ssh.cleanup()
        self.assertEqual(self.config.read_text(encoding="utf-8"), other)
        self.assertFalse(self.key.exists())

    def test_keeps_other_hosts(self):
        """Blocks of other hosts and unrelated lines are kept, every own block is removed"""
        own = block("a.example", str(self.key))
        before = "# unrelated\n" + block("b.example", "/tmp/b.pem")
        after = block("c.example", "/tmp/c.pem")
        self.config.write_text(before + own + own + after, encoding="utf-8")
        self.ssh.cleanup()
        self.assertEqual(self.config.read_text(encoding="utf-8"), before + after)

    def test_missing_key(self):
        """The config is cleaned up even when the key file is already gone"""
        self.key.unlink()
        other = block("b.example", "/tmp/b.pem")
        self.config.write_text(other + block("a.example", str(self.key)), encoding="utf-8")
        self.ssh.cleanup()
        self.assertEqual(self.config.read_text(encoding="utf-8"), other)
