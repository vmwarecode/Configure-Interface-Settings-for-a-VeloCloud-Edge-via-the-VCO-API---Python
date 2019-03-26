#!/usr/bin/env/python

from __future__ import print_function

import os
from uuid import uuid4

import velocloud
from velocloud.rest import ApiException

# If SSL verification disabled (e.g. in a development environment)
import urllib3
urllib3.disable_warnings()
velocloud.configuration.verify_ssl=False


def main():
    client = velocloud.ApiClient(host=os.environ['VCO_HOST'])
    client.authenticate(os.environ['VCO_USERNAME'], os.environ['VCO_PASSWORD'], operator=False)
    api = velocloud.AllApi(client)

    UNIQ = str(uuid4())

    enterpriseId = 5

    print('### GETTING ENTERPRISE CONFIGURATIONS ###')
    params = { 'enterpriseId': enterpriseId }
    try:
        res = api.enterpriseGetEnterpriseConfigurations(params)
    except ApiException as e:
        print(e)

    profileId = res[0].id

    print('### PROVISIONING NEW EDGE ###')
    params = { 'enterpriseId': enterpriseId,
               'name': 'TestCo Branch %s' % UNIQ,
               'description': 'A test Edge generated with a Python API client',
               'modelNumber': 'edge500',
               'configurationId': profileId }
    try:
        res = api.edgeEdgeProvision(params)
    except ApiException as e:
        print(e)

    edgeId = res.id
    print('### PROVISIONED EDGE WITH ID: %s ###' % edgeId)


    print('### GETTING EDGE CONFIGURATION STACK ###')
    params = { 'enterpriseId': enterpriseId,
               'edgeId': edgeId }
    try:
        res = api.edgeGetEdgeConfigurationStack(params)
    except ApiException as e:
        print(e)

    # The Edge-specific profile is always the first entry, convert to a dict for easy manipulation
    edgeSpecificProfile = res[0].to_dict()
    edgeSpecificProfileDeviceSettings = [m for m in edgeSpecificProfile['modules'] if m['name'] == 'deviceSettings'][0]
    edgeSpecificProfileDeviceSettingsData = edgeSpecificProfileDeviceSettings['data']
    moduleId = edgeSpecificProfileDeviceSettings['id']

    routedInterfaces = edgeSpecificProfileDeviceSettingsData['routedInterfaces']
    for iface in routedInterfaces:
        if iface['name'] == 'INTERNET2':
            iface['override'] = True
            iface['addressing'] = { 'cidrIp': '10.0.0.0',
                                    'cidrPrefix': 24,
                                    'gateway': '10.0.0.1',
                                    'netmask': '255.255.255.0',
                                    'type': 'DHCP' }

    print('### UPDATING EDGE DEVICE SETTINGS ###')
    # Post updates - update ONLY the data property in this case
    params = { 'enterpriseId': enterpriseId,
               'id': moduleId,
               '_update': { 'data':  edgeSpecificProfileDeviceSettingsData }}
    try:
        res = api.configurationUpdateConfigurationModule(params)
        print(res)
    except ApiException as e:
        print(e)

if __name__ == "__main__":
    main()
