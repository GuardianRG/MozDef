# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
from utilities.key_exists import key_exists
from utilities.toUTC import toUTC
from utilities.dot_dict import DotDict

class message(object):
    def __init__(self):
        '''
            Plugin used to fix object type discretions with cloudtrail messages
        '''
        self.registration = ['guardduty']
        self.priority = 10

        # AWS guard duty sends dates as iso_8601 which ES doesn't appreciate
        # here's a list of date fields we'll convert to isoformat
        self.date_keys = [
            'details.service.eventLastSeen',
            'details.service.eventFirstSeen',
            'details.resource.instanceDetails.launchTime',
            'details.createdAt',
            'details.updatedAt'
        ]

        # AWS guard duty can send IPs in a bunch of places
        # Lets pick out some likely targets and format them
        # so other mozdef plugins can rely on their location
        self.ipaddress_keys =[
            'details.service.action.networkConnectionAction.remoteIpDetails.ipAddressV4',
            'details.service.action.awsApiCallAction.remoteIpDetails.ipAdrressV4'
        ]

    def convert_key_date_format(self, needle, haystack):
        num_levels = needle.split(".")
        if len(num_levels) == 0:
            return False
        current_pointer = haystack
        for updated_key in num_levels:
            if updated_key == num_levels[-1]:
                current_pointer[updated_key] = toUTC(current_pointer[updated_key]).isoformat()
                return haystack
            if updated_key in current_pointer:
                current_pointer = current_pointer[updated_key]
            else:
                return haystack

    def onMessage(self, message, metadata):
        if 'source' not in message:
            return (message, metadata)

        if not message['source'] == 'guardduty':
            return (message, metadata)


        # reformat the date fields to iosformat
        for date_key in self.date_keys:
            if key_exists(date_key, message):
                message = self.convert_key_date_format(date_key, message)

        # convert the dict to a dot dict for saner deep key/value processing
        message=DotDict(message)
        # pull out the likely source IP address
        for ipaddress_key in self.ipaddress_keys:
            if 'sourceipaddress' not in message['details'].keys():
                if key_exists(ipaddress_key,message):
                    message.details.sourceipaddress = message.get(ipaddress_key)

        # recovert the message back to a plain dict
        return (dict(message), metadata)
