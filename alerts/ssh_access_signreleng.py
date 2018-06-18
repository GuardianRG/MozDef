#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch, PhraseMatch, QueryStringMatch
import re
import json


class AlertAuthSignRelengSSH(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=15)

        self.parse_config('ssh_access_signreleng.conf', ['hostfilter', 'ircchannel', 'exclusions'])

        if self.config.ircchannel == '':
            self.config.ircchannel = None

        exclusions = json.loads(self.config.exclusions)

        search_query.add_must([
            TermMatch('tags', 'releng'),
            TermMatch('details.program', 'sshd'),
            QueryStringMatch('details.hostname: /{}/'.format(self.config.hostfilter)),
            PhraseMatch('summary', 'Accepted publickey for ')
        ])

        for exclusion in exclusions:
            exclusion_query = None
            for key, value in exclusion.iteritems():
                phrase_exclusion = PhraseMatch(key, value)
                if exclusion_query is None:
                    exclusion_query = phrase_exclusion
                else:
                    exclusion_query = exclusion_query + phrase_exclusion

            search_query.add_must_not(exclusion_query)

        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'access'
        tags = ['ssh']
        severity = 'NOTICE'

        targethost = 'unknown'
        sourceipaddress = 'unknown'
        x = event['_source']
        if 'details' in x:
            if 'hostname' in x['details']:
                targethost = x['details']['hostname']
            if 'sourceipaddress' in x['details']:
                sourceipaddress = x['details']['sourceipaddress']

        targetuser = 'unknown'
        expr = re.compile('Accepted publickey for ([A-Za-z0-9]+) from')
        m = expr.match(event['_source']['summary'])
        groups = m.groups()
        if len(groups) > 0:
            targetuser = groups[0]

        summary = 'SSH login from {0} on {1} as user {2}'.format(sourceipaddress, targethost, targetuser)
        return self.createAlertDict(summary, category, tags, [event], severity, ircchannel=self.config.ircchannel)
