ARG NETBOX_VARIANT=v3.6

FROM netboxcommunity/netbox:${NETBOX_VARIANT}

RUN mkdir -pv /plugins/netbox-paas
COPY . /plugins/netbox-paas

RUN python3 /plugins/netbox-paas/setup.py develop
RUN cp -rf /plugins/netbox-paas/netbox_paas/ /opt/netbox/venv/lib/python3.11/site-packages/netbox_paas
