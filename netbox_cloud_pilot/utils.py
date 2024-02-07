import requests
import semver
import yaml
from django.conf import settings
from django.utils.safestring import mark_safe

from .constants import NETBOX_JPS_REPO

__all__ = ("get_plugins_list", "filter_releases", "job_msg", "is_upgrade_available")


def get_plugins_list():
    plugins = {}

    # Download plugins.yaml from GitHub
    response = requests.get(f"{NETBOX_JPS_REPO}/plugins.yaml")
    if response.ok:
        plugins = yaml.safe_load(response.text)

    return plugins


def is_compatible(netbox_version, min_version, max_version):
    """
    Check if the NetBox version is compatible with the plugin.
    """
    if min_version and semver.compare(netbox_version, min_version) < 0:
        return False

    if max_version and semver.compare(netbox_version, max_version) > 0:
        return False

    return True


def filter_releases(plugin, netbox_version: str = None):
    """
    Filter the releases based on the NetBox version.
    """
    compatible_releases = []
    version = netbox_version or settings.VERSION

    for release in plugin.get("releases", []):
        netbox = release.get("netbox")
        min_version = netbox.get("min")
        max_version = netbox.get("max")

        if is_compatible(version, min_version, max_version):
            compatible_releases.append(release["tag"])

    try:
        return sorted(compatible_releases, key=semver.parse_version_info, reverse=True)
    except ValueError:
        return compatible_releases


def is_upgrade_available(plugin, plugin_version: str):
    """
    Check if a newer version of the plugin is available.
    """
    releases = filter_releases(plugin, settings.VERSION)
    if not releases:
        return False

    # Check if the latest release is newer than the current version
    latest_release = releases[0]
    latest_release = latest_release.lstrip("v")
    return semver.compare(latest_release, plugin_version) > 0


def job_msg(job):
    return mark_safe(f"Job <a href='{job.get_absolute_url()}'>{job}</a> has been created successfully.")
