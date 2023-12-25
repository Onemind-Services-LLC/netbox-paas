from extras.plugins import PluginMenu
from extras.plugins import PluginMenuButton, PluginMenuItem
from utilities.choices import ButtonColorChoices

menu = PluginMenu(
    label="Netbox Cloud Pilot",
    icon_class="mdi mdi-cloud",
    groups=(
        (
            "Configurations",
            (
                PluginMenuItem(
                    link_text="Configurations",
                    link="plugins:netbox_cloud_pilot:netboxconfiguration_list",
                    permissions=["netbox_cloud_pilot.view_netboxconfiguration"],
                ),
            ),
        ),
    ),
)
