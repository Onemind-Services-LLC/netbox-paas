from extras.plugins import PluginMenu
from extras.plugins import PluginMenuButton, PluginMenuItem

menu = PluginMenu(
    label="Netbox Cloud Pilot",
    icon_class="mdi mdi-cloud",
    groups=(
        (
            "Infrastructure",
            (
                PluginMenuItem(
                    link_text="Manage",
                    link="plugins:netbox_cloud_pilot:netboxconfiguration_list",
                    permissions=["netbox_cloud_pilot.view_netboxconfiguration"],
                ),
            ),
        ),
    ),
)
