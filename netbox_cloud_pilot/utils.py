import requests
import semver
import yaml
from django.conf import settings
from django.utils.safestring import mark_safe

from .constants import NETBOX_JPS_REPO

__all__ = ("get_plugins_list", "filter_releases", "job_msg")


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


def filter_releases(plugin, version: str = None):
    """
    Filter the releases based on the NetBox version.
    """
    compatible_releases = []
    version = version or settings.VERSION

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


def job_msg(job):
    return mark_safe(f"Job <a href='{job.get_absolute_url()}'>{job}</a> has been created successfully.")
