#!/usr/bin/env/python3

import os
from uuid import uuid4
from client import *


def main():
    client = VcoRequestManager(os.environ['VCO_HOST'])
    client.authenticate(os.environ["VC_USERNAME"], os.environ["VC_PASSWORD"], is_operator=True)

    UNIQ = str(uuid4())

    enterpriseId = 1

    print('### GETTING ENTERPRISE CONFIGURATIONS ###')
    params = { 'enterpriseId': enterpriseId }
    try:
        res = client.call_api('enterprise/getEnterpriseConfigurations', params)
    except ApiException as e:
        print(e)

    profileId = res[0]['id']

    print('### PROVISIONING NEW EDGE ###')
    params = { 'enterpriseId': enterpriseId,
               'name': 'TestCo Branch %s' % UNIQ,
               'description': 'A test Edge generated with a Python API client',
               'modelNumber': 'edge500',
               'configurationId': profileId }
    try:
        res = client.call_api('edge/edgeProvision', params)
    except ApiException as e:
        print(e)

    edgeId = res['id']
    print('### PROVISIONED EDGE WITH ID: %s ###' % edgeId)


    print('### GETTING EDGE CONFIGURATION STACK ###')
    params = { 'enterpriseId': enterpriseId,
               'edgeId': edgeId }
    try:
        res = client.call_api('edge/getEdgeConfigurationStack', params)
    except ApiException as e:
        print(e)

    # The Edge-specific profile is always the first entry, convert to a dict for easy manipulation
    edgeSpecificProfile = res[0]
    edgeSpecificProfileDeviceSettings = [m for m in edgeSpecificProfile['modules'] if m['name'] == 'deviceSettings'][0]
    edgeSpecificProfileDeviceSettingsData = edgeSpecificProfileDeviceSettings['data']
    moduleId = edgeSpecificProfileDeviceSettings['id']

    # For newly-provisioned Edges we need to specify a VLAN address space
    edgeSpecificProfileDeviceSettingsData['lan']['networks'][0]['cidrIp'] = '10.0.0.1'
    routedInterfaces = edgeSpecificProfileDeviceSettingsData['routedInterfaces']
    for iface in routedInterfaces:
        if iface['name'] == 'INTERNET2':
            iface['addressing'] = { 'cidrIp': '20.0.0.0',
                                    'cidrPrefix': 24,
                                    'gateway': '20.0.0.1',
                                    'netmask': '255.255.255.0',
                                    'type': 'STATIC' }

    print('### UPDATING EDGE DEVICE SETTINGS ###')
    # Post updates - update ONLY the data property in this case
    params = { 'enterpriseId': enterpriseId,
               'id': moduleId,
               '_update': { 'data':  edgeSpecificProfileDeviceSettingsData }}
    try:
        res = client.call_api('configuration/updateConfigurationModule', params)
        print(res)
    except ApiException as e:
        print(e)

if __name__ == "__main__":
    main()