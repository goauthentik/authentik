from authentik.endpoints.connector import BaseConnector
from authentik.endpoints.connectors.agent.models import AgentConnector as DBC


class AgentConnector(BaseConnector[DBC]):

    def supported_enrollment_methods(self):
        return []
