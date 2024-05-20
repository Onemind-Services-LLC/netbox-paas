import os
from importlib.metadata import metadata

from extras.plugins import PluginConfig

metadata = metadata("netbox_paas")


class NetBoxPaas(PluginConfig):
    name = metadata.get("Name").replace("-", "_")
    verbose_name = metadata.get("Name")
    description = metadata.get("Summary")
    version = metadata.get("Version")
    author = metadata.get("Author")
    author_email = metadata.get("Author-email")
    base_url = "paas"
    min_version = "3.7.0"
    max_version = "3.7.99"

    def ready(self):
        super().ready()

        # Ensure ENV_NAME is set in the environment
        if not os.environ.get("ENV_NAME"):
            raise Exception("ENV_NAME is not set in the environment")


config = NetBoxPaas
