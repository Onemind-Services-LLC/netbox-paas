ARG NETBOX_VARIANT=v3.6

FROM netboxcommunity/netbox:${NETBOX_VARIANT}

RUN mkdir -pv /plugins/netbox-cloud-pilot
COPY . /plugins/netbox-cloud-pilot

RUN python3 /plugins/netbox-cloud-pilot/setup.py develop
RUN cp -rf /plugins/netbox-cloud-pilot/netbox_paas/ /opt/netbox/venv/lib/python3.11/site-packages/netbox_paas
