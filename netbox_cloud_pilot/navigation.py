from extras.plugins import PluginMenu
from extras.plugins import PluginMenuButton, PluginMenuItem

menu = PluginMenu(
    label="Netbox Cloud Pilot",
    icon_class="mdi mdi-cloud",
    groups=(
        (
            "",
            (
                PluginMenuItem(
                    link_text="Manage",
                    link="plugins:netbox_cloud_pilot:netboxconfiguration_list",
                    permissions=["netbox_cloud_pilot.view_netboxconfiguration"],
                ),
                PluginMenuItem(
                    link_text="DB Backups",
                    link="plugins:netbox_cloud_pilot:netboxdbbackup_list",
                    permissions=["netbox_cloud_pilot.change_netboxconfiguration"],
                ),
                PluginMenuItem(
                    link_text="Plugins Store",
                    link="plugins:netbox_cloud_pilot:netboxplugin_list",
                    permissions=["netbox_cloud_pilot.view_netboxconfiguration"],
                ),
            ),
        ),
    ),
)
