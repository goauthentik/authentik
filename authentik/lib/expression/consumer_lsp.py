from textwrap import indent
from typing import Iterable
from channels.generic.websocket import JsonWebsocketConsumer
from pylsp.python_lsp import PythonLSPServer


class AuthentikPythonLSP(PythonLSPServer):

    def m_initialize(
        self,
        processId=None,
        rootUri=None,
        rootPath=None,
        initializationOptions=None,
        workspaceFolders=None,
        **_kwargs,
    ):
        _kwargs["capabilities"] = {}
        response = super().m_initialize(
            processId, rootUri, rootPath, initializationOptions={
                "pylsp.plugins.jedi.auto_import_modules": [],
                "pylsp.plugins.jedi_completion.eager": True,
            }, workspaceFolders=None, **_kwargs
        )
        return response


class LSPConsumer(JsonWebsocketConsumer):

    handler_class = AuthentikPythonLSP

    handler: PythonLSPServer

    def connect(self):
        self.accept()
        self.handler = self.handler_class(None, None, consumer=self.send_json)

    def disconnect(self, code):
        pass

    def wrap_expression(self, expression: str, params: Iterable[str]) -> str:
        """Wrap expression in a function, call it, and save the result as `result`"""
        handler_signature = ",".join(params)
        full_expression = ""
        full_expression += "from authentik.policies.types import PolicyRequest\n"
        full_expression += f"def handler({handler_signature}):\n"
        full_expression += indent(expression, "    ")
        full_expression += f"\nresult = handler({handler_signature})"
        return full_expression

    def send_json(self, content, close=False):
        print(self.handler.config)
        return super().send_json(content, close)

    def receive_json(self, content, **kwargs):
        if content.get("method", "") == "textDocument/didOpen":
            textDocument = content.get("params",{}).get("textDocument", {})
            text = textDocument.get("text")
            if text:
                textDocument["text"] = self.wrap_expression(text, ["request: PolicyRequest"])
        if content.get("method", "") == "textDocument/didChange":
            contentChanges = content.get("params", {}).get("contentChanges", [""])
            text = contentChanges[0].get("text", "")
            if text:
                contentChanges[0]["text"] = self.wrap_expression(text, ["request: PolicyRequest"])
        self.handler.consume(content)
        # print(self.handler.config.plugin_manager.get_plugins())
        print(self.handler.config.plugin_settings("jedi_completion"))
