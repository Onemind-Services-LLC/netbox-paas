ARG NETBOX_VARIANT=v3.5

FROM netboxcommunity/netbox:${NETBOX_VARIANT}

RUN mkdir -pv /plugins/netbox-cloud-pilot
COPY . /plugins/netbox-cloud-pilot

RUN python3 /plugins/netbox-cloud-pilot/setup.py develop
RUN cp -rf /plugins/netbox-cloud-pilot/netbox_cloud_pilot/ /opt/netbox/venv/lib/python3.10/site-packages/netbox_cloud_pilot
