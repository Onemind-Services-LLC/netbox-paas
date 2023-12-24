ARG NETBOX_VARIANT=v3.5

FROM registry.tangience.net/netbox/netbox:${NETBOX_VARIANT}

USER root

# Remove Script and Report folder
RUN find $APP_USER_HOME/netbox/scripts -type f ! -name '__init__.py' -exec rm -v {} +
RUN find $APP_USER_HOME/netbox/reports -type f ! -name '__init__.py' -exec rm -v {} +

# Remove pre-installed plugin
RUN rm -rf /usr/local/lib/python3.10/site-packages/netbox_cloud_pilot

RUN mkdir -pv /plugins/netbox-cloud-pilot
COPY . /plugins/netbox-cloud-pilot

RUN python3 /plugins/netbox-cloud-pilot/setup.py develop
RUN cp -rf /plugins/netbox-cloud-pilot/netbox_cloud_pilot/ /usr/local/lib/python3.10/site-packages/netbox_cloud_pilot

USER $USER
