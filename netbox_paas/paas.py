import logging
import time
from functools import lru_cache
from typing import Tuple

import requests
import yaml
from django.conf import settings
from jelastic import Jelastic
from jelastic.api.exceptions import JelasticApiError
from requirements import parse as requirements_parse
from requirements.parser import Requirement
from semver.version import Version

from core.choices import JobStatusChoices
from core.models import Job
from netbox.config import get_config
from . import utils
from .constants import JELASTIC_API, NODE_GROUP_CP, NODE_GROUP_SQLDB, DISABLED_PLUGINS_FILE_NAME, PLUGINS_FILE_NAME

logger = logging.getLogger("netbox_paas")

__all__ = (
    "PaaS",
    "PaaSNetBox",
)


class RequirementsParser:
    """
    This class is used to parse the requirements.txt file.
    """

    def __init__(self, req_str: str):
        self.requirements = self.loads(req_str)

    @staticmethod
    def loads(req_str: str) -> list[Requirement]:
        """
        Parse the requirements.txt file.
        """
        return list(requirements_parse(req_str))

    def _exists(self, req: Requirement) -> bool:
        """
        Check if a requirement exists.
        """
        for r in self.requirements:
            if req.vcs:
                if r.vcs == req.vcs and r.uri == req.uri:
                    return True
            else:
                if r.name == req.name:
                    return True

        return False

    def add(self, req_str: str) -> bool:
        """
        Add a requirement to the requirements.txt file.
        """
        # Check if the requirement already exists
        req = self.loads(req_str)[0]

        # Update the requirement if it already exists, else add a new one
        for i, existing_req in enumerate(self.requirements):
            if existing_req.name == req.name:
                self.requirements[i] = req  # Update in-place
                return True

        self.requirements.append(req)  # Add new requirement
        return True

    def remove(self, req_str: str) -> bool:
        """
        Remove a requirement from the requirements.txt file.
        """
        # Check if the requirement exists
        req = self.loads(req_str)[0]

        # It is possible that req does not contain a version, so we need to check if it exists in the requirements
        if not self._exists(req):
            return False

        self.requirements = [r for r in self.requirements if r.name != req.name]
        return True

    def dumps(self) -> str:
        """
        Dump the requirements.txt file.
        """
        return "\n".join([str(r.line) for r in self.requirements])


class PaaSJob:
    @classmethod
    def enqueue(cls, func, model, request=None, *args, **kwargs):
        """
        Enqueue a job to be executed asynchronously.
        """
        logger.info(f"Enqueuing job {func.__name__}")

        kwargs["_func"] = func

        return Job.enqueue(
            cls._run_job,
            model,
            name=func.__name__,
            user=request.user if request else None,
            job_timeout=settings.RQ_DEFAULT_TIMEOUT,
            **kwargs,
        )

    @staticmethod
    def _run_job(job, *args, **kwargs):
        """
        Run a job.
        """
        data = {"params": kwargs}

        # Start the job
        try:
            job.start()
            func = kwargs.pop("_func")
            result = func(*args, **kwargs)

            data.update({"result": result})

            job.terminate()
        except Exception as e:  # pylint: disable=broad-except
            logger.exception(e)
            data.update({"error": str(e)})
            job.terminate(status=JobStatusChoices.STATUS_ERRORED)

        job.data = data
        job.save()


class PaaS(PaaSJob):
    """
    This class is used to manage the PaaS layer of the Jelastic platform.
    """

    def __init__(self, token: str, env_name: str, auto_init: bool = True):
        self.admin_url = JELASTIC_API
        self.client = Jelastic(base_url=self.admin_url, token=token)
        self.env_name = env_name

        if auto_init:
            self._get_env_info()
        logger.debug(f"PaaS layer initialized for environment {self.env_name}")

    @lru_cache(maxsize=1)
    def _get_env_info(self):
        """
        Get information about the environment.
        """
        logger.debug("Getting environment information")
        return self.client.environment.Control.GetEnvInfo(env_name=self.env_name)

    @lru_cache(maxsize=10)
    def _get_env_var(self, node_group):
        """
        Get environment variables for a node group.
        """
        logger.debug(f"Getting environment variables for node group {node_group}")
        return self.client.environment.Control.GetContainerEnvVarsByGroup(
            env_name=self.env_name, node_group=node_group
        ).get("object", {})

    def clear_cache(self):
        """
        Clear the cache.
        """
        logger.debug("Clearing cache")
        self._get_env_info.cache_clear()
        self._get_env_var.cache_clear()

    def get_env(self):
        """
        Get the environment.
        """
        return self._get_env_info()["env"]

    def get_nodes(self, node_group: str = None, is_master: bool = True) -> dict | list:
        """
        Get the environment nodes.
        """
        logger.debug(f"Getting nodes for node group {node_group}, is_master={is_master}")
        nodes = self._get_env_info().get("nodes", [])
        if node_group:
            nodes = [node for node in nodes if node["nodeGroup"] == node_group]
        if is_master:
            try:
                nodes = [node for node in nodes if node["ismaster"]][0]
            except IndexError:
                nodes = {}
        return nodes

    def get_node_groups(self):
        """
        Get the environment node groups.
        """
        node_groups = sorted(
            self._get_env_info().get("nodeGroups", {}),
            key=lambda x: x.get("displayName", x.get("name")),
        )

        # For each node group, get the related nodes
        for node_group in node_groups:
            node_group["node"] = self.get_nodes(node_group=node_group["name"], is_master=True)

        return node_groups

    def get_node(self, node_id):
        """
        Get a node by its ID.
        """
        logger.debug(f"Getting node {node_id} for environment {self.env_name}")
        nodes = self._get_env_info().get("nodes", [])
        return next((node for node in nodes if str(node["id"]) == node_id), None)

    def get_external_domains(self):
        """
        Get the external domains.
        """
        logger.debug(f"Getting external domains for environment {self.env_name}")
        return self._get_env_info().get("extdomains", [])

    def is_ssl_enabled(self):
        """
        Check if SSL is enabled.
        """
        logger.debug(f"Checking if built-in SSL is enabled for environment {self.env_name}")
        return self.get_env().get("sslstate", False)

    def get_node_log(self, node_id, path="/var/log/run.log"):
        """
        Get the logs of a node.
        """
        logger.debug(f"Getting log for node {node_id} for environment {self.env_name}")
        return self.client.environment.Control.ReadLog(env_name=self.env_name, node_id=node_id, path=path).get(
            "body", ""
        )

    def get_url(self):
        """
        Get the environment URL.
        """
        logger.debug(f"Getting URL for environment {self.env_name}")
        scheme = "https" if self.is_ssl_enabled() else "http"
        if ext_domains := self.get_external_domains():
            return f"{scheme}://{ext_domains[0]}"

        domain = self.get_env().get("domain", "")
        return f"{scheme}://{domain}"

    def get_addons(self, node_group, search=None):
        """
        Get the addons for a node group.
        """
        logger.debug(f"Getting addons for node group {node_group}")
        return self.client.marketplace.App.GetAddonList(
            env_name=self.env_name, node_group=node_group, search=search
        ).get("apps", [])

    def get_installed_addon(self, app_id, node_group, search=None):
        """
        Get the installed addon for a node group.
        """
        logger.debug(f"Checking if addon ({app_id}) is installed for node group {node_group}")
        addons = self.get_addons(node_group=node_group, search=search)

        return next(
            (addon for addon in addons if addon["app_id"] == app_id and addon.get("isInstalled", False)),
            None,
        )

    def add_env_vars(self, node_group, env_vars):
        """
        Add environment variables to a node group.
        """
        logger.debug(f"Adding environment variables to node group {node_group}")
        return self.client.environment.Control.AddContainerEnvVars(
            env_name=self.env_name, node_group=node_group, vars=env_vars
        )

    def get_env_vars(self, node_group):
        """
        Get environment variables for a node group.
        """
        logger.debug(f"Getting environment variables for node group {node_group}")
        return self.client.environment.Control.GetContainerEnvVarsByGroup(
            env_name=self.env_name, node_group=node_group
        ).get("object", {})

    def remove_env_vars(self, node_group, env_vars: list[str]):
        """
        Remove environment variables from a node group.
        """
        logger.debug(f"Removing environment variables from node group {node_group}")
        return self.client.environment.Control.RemoveContainerEnvVars(
            env_name=self.env_name, node_group=node_group, vars=env_vars
        )

    def run_script(self, name, code, description=None, params=None, delay=10):
        """
        Run a script.
        """
        app_id = self.get_env().get("appid")
        delay = delay * 1000

        try:
            result = self.client.development.Scripting.GetScripts(
                app_id=app_id,
                type="js",
            )
            scripts = result.get("scripts", [])
            for script in scripts:
                if script.get("name") == name:
                    logger.debug(f"Deleting existing script {name}")
                    self.client.development.Scripting.DeleteScript(app_id=app_id, name=name)
                    continue
        except JelasticApiError as e:
            logger.error(e)

        self.client.development.Scripting.CreateScript(app_id=app_id, name=name, type="js", code=code)

        return self.client.utils.Scheduler.CreateEnvTask(
            env_name=self.env_name,
            script=name,
            trigger={"once_delay": delay},
            description=description,
            params=params,
        )

    def restart_nodes(self, node_groups: list[str], lazy: bool = False, delay: int = 10):
        """
        Restart nodes for a list of node groups.
        """
        # Sort the node groups in ascending order
        node_groups = sorted(node_groups)

        results = []

        logger.debug(f"Restarting nodes for node groups {', '.join(node_groups)}")
        if lazy:
            for node_group in node_groups:
                script_name = f"ncp-restart-{node_group}"
                script_code = """
                var c = jelastic.environment.control, e = envName, s = session, r, resp;
                resp = c.GetEnvInfo(e, s);
                if (resp.result != 0) return resp;
                r = c.RestartNodes({ envName: e, session: s, nodeGroup: nodeGroup, isSequential: true, manageDnsState: true, delay: 60000 });
                if (r.result != 0) return r;
                return { result: 0, message: 'Restarted ' + nodeGroup}
                """

                task_result = self.run_script(
                    name=script_name,
                    code=script_code,
                    description=f"Restart {node_group} nodes",
                    params={"envName": self.env_name, "nodeGroup": node_group},
                    delay=delay if node_group == NODE_GROUP_CP else delay * 10,
                )
                results.append(task_result)

            return results

        for node_group in node_groups:
            task_result = self.client.environment.Control.RestartNodes(
                env_name=self.env_name,
                node_group=node_group,
                is_sequential=True,
                manage_dns_state=True,
                delay=delay,
            )
            results.append(task_result)

        return results

    def execute_cmd(self, node_id, command):
        """
        Execute a command on a node.
        """
        logger.debug(f"Executing command {command} on node {node_id}")
        return self.client.environment.Control.ExecCmdById(
            env_name=self.env_name,
            node_id=node_id,
            command_list=[
                {
                    "command": command,
                }
            ],
        ).get("responses", [])

    def execute_action(self, app_unique_name, action="configure", params=None):
        """
        Execute an action on an addon.
        """
        logger.info(f"Executing action {action} on addon {app_unique_name}")
        return self.client.marketplace.Installation.ExecuteAction(
            app_unique_name=app_unique_name,
            action=action,
            params=params,
        )

    def install_addon(self, app_id, node_group, addon_settings=None):
        """
        Install an addon.
        """
        # Check if the addon is already installed
        if addon := self.get_installed_addon(app_id=app_id, node_group=node_group):
            logger.info(f"Addon {app_id} is already installed")
            return self.execute_action(
                app_unique_name=addon.get("uniqueName"),
                params=addon_settings,
            )

        logger.info(f"Installing addon {app_id}")
        return self.client.marketplace.App.InstallAddon(
            env_name=self.env_name,
            id=app_id,
            settings=addon_settings,
            node_group=node_group,
        )

    def uninstall_addon(self, app_id, node_group, search=None):
        """
        Uninstall an addon.
        """
        # Check if the addon is already installed
        if addon := self.get_installed_addon(app_id=app_id, node_group=node_group, search=search):
            logger.info(f"Uninstalling addon {app_id}")

            return self.client.marketplace.Installation.Uninstall(
                app_unique_name=addon.get("uniqueName"),
                target_app_id=self.get_env().get("appid"),
                app_template_id=app_id,
            )

        msg = f"Addon {app_id} is not installed on node group {node_group}."
        logger.info(msg)
        return {"result": 0, "message": msg}

    def get_master_node(self, node_group):
        return self.get_nodes(node_group=node_group, is_master=True)

    def get_actions(self):
        actions = self.client.environment.Tracking.GetCurrentActions().get("array", [])
        return [action for action in actions if action.get("text", {}).get("env") == self.env_name]


class PaaSNetBox(PaaS):
    """
    This class is used to manage the PaaS layer of the Jelastic platform for NetBox.
    """

    NETBOX_DIR = '/etc/netbox'

    def get_nb_node_groups(self):
        """
        Get the environment node groups for NetBox.
        """
        results = []

        node_groups = self.get_node_groups()

        # For each node group, get the related nodes
        for node_group in node_groups:
            if "netbox" in node_group.get("node", {}).get("customitem", {}).get("dockerName"):
                results.append(node_group)

        return results

    def load_plugins(self, file_name="plugins.yaml"):
        """
        Loads the plugins from the plugins.yaml file.
        """
        master_node_id = self.get_master_node(NODE_GROUP_CP).get("id")

        try:
            file_path = f"{self.NETBOX_DIR}/config/{file_name}"
            plugins_yaml = self.execute_cmd(master_node_id, f"cat {file_path}")[0].get("out", "")
        except JelasticApiError:
            plugins_yaml = ""

        return yaml.safe_load(plugins_yaml) or {}

    def dump_plugins(self, plugins, file_name="plugins.yaml"):
        """
        Dumps the plugins to the plugins.yaml file.
        """
        master_node_id = self.get_master_node(NODE_GROUP_CP).get("id")
        plugins_yaml = yaml.dump(plugins)

        self.client.environment.File.Write(
            env_name=self.env_name,
            path=f"{self.NETBOX_DIR}/config/{file_name}",
            body=plugins_yaml,
            node_id=master_node_id,
            is_append_mode=False,
        )

    def get_requirements_parser(self):
        master_node_id = self.get_master_node(NODE_GROUP_CP).get('id')
        requirements_str = self.execute_cmd(master_node_id, f'cat {self.NETBOX_DIR}/plugin_requirements.txt')[0].get(
            'out', ''
        )
        return RequirementsParser(requirements_str)

    def write_requirements(self, req: RequirementsParser):
        master_node_id = self.get_master_node(NODE_GROUP_CP).get('id')
        requirements_str = req.dumps()
        return self.client.environment.File.Write(
            env_name=self.env_name,
            node_id=master_node_id,
            body=requirements_str,
            path=f'{self.NETBOX_DIR}/plugin_requirements.txt',
            is_append_mode=False,
        )

    def install_plugin(
        self,
        plugin: dict,
        version,
        plugin_settings=None,
        github_token=None,
        restart: bool = True,
        collectstatic: bool = True,
        install: bool = True,
    ):
        activate_env = "source /opt/netbox/venv/bin/activate"
        # Get all node IDs for the NetBox node groups
        node_ids = [
            node["id"]
            for node_group in self.get_nb_node_groups()
            for node in self.get_nodes(node_group=node_group["name"], is_master=False)
        ]

        # Install the plugin version
        if plugin.get("private"):
            github_url = plugin.get("github_url")
            github_url = github_url.replace("https://github.com", f"git+https://{github_token}@github.com")

            plugin_req = f'{github_url}@{version}'
        else:
            plugin_req = f'{plugin.get("name")}=={version}'

        req = self.get_requirements_parser()
        if req.add(plugin_req):
            self.write_requirements(req)

            if install:
                if plugin.get("private"):
                    # Ensure `git` is installed on every node
                    [self.execute_cmd(node_id, "apt-get install -y git") for node_id in node_ids]

                # Install the plugin
                cmd = f'{activate_env} && pip install -r {self.NETBOX_DIR}/plugin_requirements.txt'
                [self.execute_cmd(node_id, cmd) for node_id in node_ids]

        plugins = self.load_plugins()
        disabled_plugins = self.load_plugins(file_name=DISABLED_PLUGINS_FILE_NAME)

        if plugin.get("app_label") in disabled_plugins:
            disabled_plugins.pop(plugin.get("app_label"))
            self.dump_plugins(disabled_plugins, file_name=DISABLED_PLUGINS_FILE_NAME)

        plugins[plugin.get("app_label")] = plugin_settings or {}
        self.dump_plugins(plugins)

        if collectstatic:
            # Get Node IDs for the CP node group
            cp_node_ids = [node["id"] for node in self.get_nodes(node_group=NODE_GROUP_CP, is_master=False)]
            # Run collectstatic command
            [
                self.execute_cmd(
                    node_id=node_id,
                    command=f"{activate_env} && /opt/netbox/netbox/manage.py collectstatic --no-input --clear 1>/dev/null",
                )
                for node_id in cp_node_ids
            ]

        if restart:
            return self.restart_nodes(
                node_groups=[node_group["name"] for node_group in self.get_nb_node_groups()],
                lazy=True,
            )

        return {"result": 0, "message": "Plugin installed"}

    def uninstall_plugin(self, plugin: dict):
        """
        Uninstall an addon for NetBox.
        """
        # Remove the plugin from the plugins.yaml or disabled_plugins.yaml file
        plugins = self.load_plugins()
        disabled_plugins = self.load_plugins(file_name=DISABLED_PLUGINS_FILE_NAME)

        if plugin.get("app_label") in plugins:
            plugins.pop(plugin.get("app_label"))
            self.dump_plugins(plugins)
        elif plugin.get("app_label") in disabled_plugins:
            disabled_plugins.pop(plugin.get("app_label"))
            self.dump_plugins(disabled_plugins, file_name=DISABLED_PLUGINS_FILE_NAME)

        # Uninstall the plugin from the virtual environment
        master_node_id = self.get_master_node(NODE_GROUP_CP).get("id")
        activate_env = "source /opt/netbox/venv/bin/activate"

        req = self.get_requirements_parser()
        if req.remove(plugin.get("name")):
            self.write_requirements(req)

            # Get all node IDs for the NetBox node groups
            node_ids = [
                node["id"]
                for node_group in self.get_nb_node_groups()
                for node in self.get_nodes(node_group=node_group["name"], is_master=False)
            ]

            # Uninstall the plugin
            cmd = f'{activate_env} && pip uninstall -y {plugin.get("name")}'
            for node_id in node_ids:
                self.execute_cmd(node_id, cmd)

        return self.restart_nodes(
            node_groups=[node_group["name"] for node_group in self.get_nb_node_groups()],
            lazy=True,
        )

    def _enable_disable_plugin(self, plugin: dict, source_file: str, dest_file: str):
        """
        Move a plugin from one file (source) to another (destination).
        """
        # Load source and destination plugin lists
        source_plugins = self.load_plugins(file_name=source_file)
        dest_plugins = self.load_plugins(file_name=dest_file)

        app_label = plugin.get("app_label")
        if app_label in source_plugins:
            # Move the plugin
            dest_plugins[app_label] = source_plugins.pop(app_label)
            # Update the files
            self.dump_plugins(source_plugins, file_name=source_file)
            self.dump_plugins(dest_plugins, file_name=dest_file)

    def disable_plugin(self, plugin: dict):
        """
        Disable a plugin for NetBox.
        """
        self._enable_disable_plugin(plugin, PLUGINS_FILE_NAME, DISABLED_PLUGINS_FILE_NAME)
        return self.restart_nodes(
            node_groups=[node_group["name"] for node_group in self.get_nb_node_groups()],
            lazy=True,
        )

    def enable_plugin(self, plugin: dict):
        """
        Enable a plugin for NetBox.
        """
        self._enable_disable_plugin(plugin, DISABLED_PLUGINS_FILE_NAME, PLUGINS_FILE_NAME)
        return self.restart_nodes(
            node_groups=[node_group["name"] for node_group in self.get_nb_node_groups()],
            lazy=True,
        )

    def get_env_var(self, variable, default=None):
        """
        Get the environment variable for NetBox.
        """
        container_vars = self._get_env_var(NODE_GROUP_CP)
        return getattr(get_config(), variable, container_vars.get(variable, None)) or default

    def _get_docker_tags(self):
        """
        Get the Docker tags for NetBox.
        """
        master_node = self.get_master_node(NODE_GROUP_CP)
        docker = master_node.get("customitem", {})

        if not docker:
            return []

        response = requests.get(f'https://hub.docker.com/v2/repositories/{docker["dockerName"]}/tags?page_size=1000')
        response.raise_for_status()
        response = response.json()

        names = [d["name"] for d in response["results"] if d["name"].startswith("v")]
        tags = []
        for name in names:
            try:
                version = Version.parse(name.lstrip("v"))
                if not version.prerelease:
                    tags.append(version)
            except ValueError:
                pass

        return tags

    def get_upgrades(self, include_patch: bool = False):
        """
        Get the available upgrades for NetBox.
        """
        docker_tags = self._get_docker_tags()
        current_version = Version.parse(settings.VERSION)

        upgrades = []
        for tag in docker_tags:
            if include_patch:
                if tag.major == current_version.major and tag.minor == current_version.minor:
                    upgrades.append(tag)
            if tag > current_version:
                upgrades.append(tag)

        return upgrades

    def is_upgrade_available(self):
        """
        Check if an upgrade is available for NetBox.
        """
        return bool(self.get_upgrades())

    def is_db_backup_running(self, app_unique_name):
        # Get current running actions
        for action in self.get_actions():
            action_parameters = action.get("parameters", {})

            if (
                action_parameters.get("appUniqueName") == app_unique_name
                and action_parameters.get("action") == "backup"
            ):
                return True

        return False

    def db_backup(self, app_unique_name):
        """
        Backup NetBox database.
        """
        while self.is_db_backup_running(app_unique_name=app_unique_name):
            logger.debug("Waiting for database backup to finish...")
            time.sleep(30)

        return self.execute_action(app_unique_name=app_unique_name, action="backup")

    def upgrade_checks(self, version) -> Tuple[bool, str]:
        """
        Run upgrade checks for NetBox.
        """
        # Fetch the plugins from the store
        plugins = utils.get_plugins_list()
        for plugin_name, plugin in plugins.items():
            if plugin.get("app_label") in settings.PLUGINS:
                if not utils.filter_releases(plugin, version):
                    return (
                        False,
                        f"Plugin {plugin_name} does not have a release for version {version}",
                    )

        return True, ""

    def upgrade(self, version, lic=None):
        """
        Upgrade NetBox.
        """
        activate_env = "source /opt/netbox/venv/bin/activate"
        master_node_id = self.get_master_node(NODE_GROUP_CP).get("id")
        env_app_id = self.get_env().get("appid")

        if addon := self.get_installed_addon(app_id="db-backup", node_group=NODE_GROUP_SQLDB):
            self.db_backup(app_unique_name=addon.get("uniqueName"))

        # Upgrade all plugins to the latest compatible version first without restarting the nodes
        for plugin_name, plugin in utils.get_plugins_list().items():
            if plugin.get('app_label') in settings.PLUGINS:
                plugin_version = utils.filter_releases(plugin, version)[0]
                self.install_plugin(
                    plugin=plugin,
                    version=plugin_version,
                    plugin_settings=settings.PLUGINS_CONFIG.get(plugin.get('app_label'), {}),
                    github_token=lic,
                    restart=False,
                    collectstatic=False,  # Do not run during upgrade as it may crash due to version incompatibility
                    install=False,  # Do not install the plugin as it will be installed during the upgrade
                )

        logger.info(f"Upgrading NetBox {NODE_GROUP_CP} nodes to version v{version}")
        self.client.environment.Control.RedeployContainersByGroup(
            env_name=self.env_name,
            node_group=NODE_GROUP_CP,
            tag=f"v{version}",
            use_existing_volumes=True,
            manage_dns_state=True,
            is_sequential=True,
            delay=60000,
        )

        # Run collectstatic command
        self.execute_cmd(
            node_id=master_node_id,
            command=f"{activate_env} && /opt/netbox/netbox/manage.py collectstatic --no-input --clear 1>/dev/null",
        )

        # Get all node groups except the CP node group
        node_groups = [
            node_group["name"] for node_group in self.get_nb_node_groups() if node_group["name"] != NODE_GROUP_CP
        ]
        redeploy_script = """
        import com.hivext.api.Response;

        function checkEnvStatus() {
            let retries = 0, waitInterval = (interval * 1000), resp, c = jelastic.environment.control, e = envName, s = session, r
            do {
                java.lang.Thread.sleep(retries ? waitInterval : 0)
                resp = api.env.control.GetEnvInfo({ envName: envName, lazy: true })
                if (resp.result != 0 && resp.result != Response.APPLICATION_NOT_EXIST) return resp;
                api.marketplace.console.WriteLog(logPrefix + " [" + (retries + 1) + "/"+ maxRetries + "] checking " + envName + " status result: " + (resp.env ? resp.env.status : resp ));
            } while (resp.result != Response.APPLICATION_NOT_EXIST && resp.env.status != 1 && (++retries < maxRetries))
        }

        function checkCurrentActions() {
            let retries = 0, waitInterval = (interval * 1000), resp, c = jelastic.environment.tracking, e = envName, s = session, r
            do {
                java.lang.Thread.sleep(retries ? waitInterval: 0)
                resp = api.env.tracking.GetCurrentActions()
                if (resp.result != 0) return resp;
                var currentActions = resp.array.filter(function(action) {
                    return action.text && action.text.env == envName
                })
                if (!currentActions.length) break;
                api.marketplace.console.WriteLog(logPrefix + " [" + (retries + 1) + "/"+ maxRetries + "] waiting for " + envName + " actions to finish");
            } while (++retries < maxRetries)
        }

        checkEnvStatus();
        checkCurrentActions();

        api.marketplace.console.WriteLog("RedeployContainers: " + nodeGroup);
        return api.env.control.RedeployContainersByGroup({ envName: envName, session: session, nodeGroup: nodeGroup, tag: tag, useExistingVolumes: true, manageDnsState: true, isSequential: true });
        """

        batch_request = {
            "alias": {"m": "Dev.Scripting.EvalCode"},
            "global": {"appid": env_app_id, "session": self.client._token, "type": "js", "code": redeploy_script},
            "methods": [],
        }

        for node_group in node_groups:
            batch_request["methods"].append(
                {
                    "m": {
                        "params": {
                            "envName": self.env_name,
                            "nodeGroup": node_group,
                            "tag": f"v{version}",
                            "maxRetries": 100,
                            "interval": 60,
                            "logPrefix": node_group,
                        }
                    }
                }
            )

        batch_code = f"""
        let resp = api.utils.batch.Call(appid, toJSON({batch_request}), true);
        if (resp.result != 0) return resp;
        """

        self.run_script(
            name="ncp-upgrade-netbox",
            description=f"Upgrading NetBox nodes to version v{version}",
            code=batch_code,
            delay=10,
        )
