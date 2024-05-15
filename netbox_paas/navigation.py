from extras.plugins import PluginMenu
from extras.plugins import PluginMenuItem

menu = PluginMenu(
    label="Netbox PAAS",
    icon_class="mdi mdi-cloud",
    groups=(
        (
            "",
            (
                PluginMenuItem(
                    link_text="Manage",
                    link="plugins:netbox_paas:netboxconfiguration_list",
                    permissions=["netbox_paas.view_netboxconfiguration"],
                ),
                PluginMenuItem(
                    link_text="DB Backups",
                    link="plugins:netbox_paas:netboxdbbackup_list",
                    permissions=["netbox_paas.change_netboxconfiguration"],
                ),
                PluginMenuItem(
                    link_text="Plugins Store",
                    link="plugins:netbox_paas:netboxplugin_list",
                    permissions=["netbox_paas.view_netboxconfiguration"],
                ),
            ),
        ),
    ),
)
