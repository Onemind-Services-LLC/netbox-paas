import os
from importlib.metadata import metadata

from extras.plugins import PluginConfig

metadata = metadata("netbox_paas")


class NetBoxCloudPilot(PluginConfig):
    name = metadata.get("Name").replace("-", "_")
    verbose_name = metadata.get("Name")
    description = metadata.get("Summary")
    version = metadata.get("Version")
    author = metadata.get("Author")
    author_email = metadata.get("Author-email")
    base_url = "cloud-pilot"
    min_version = "3.6.0"
    max_version = "3.6.99"

    def ready(self):
        super().ready()

        # Ensure ENV_NAME is set in the environment
        if not os.environ.get("ENV_NAME"):
            raise Exception("ENV_NAME is not set in the environment")


config = NetBoxCloudPilot
