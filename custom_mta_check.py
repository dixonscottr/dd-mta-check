import time
import requests

from bs4 import BeautifulSoup

try:
    # first, try to import the base class from new versions of the Agent...
    from datadog_checks.base import AgentCheck
except ImportError:
    # ...if the above failed, the check is running in Agent version < 6.6.0
    from checks import AgentCheck

import hashlib


class MTACheck(AgentCheck):

    def __init__(self, name, init_config, agentConfig, instances=None):
        AgentCheck.__init__(self, name, init_config, agentConfig, instances=instances)
        self.lines_running = 0
        self.last_ping = time.time()
        self.saved_line_statuses = {
            '1': 'first check',
            '2': 'first check',
            '3': 'first check',
            '4': 'first check',
            '5': 'first check',
            '6': 'first check',
            '6X': 'first check',
            '7': 'first check',
            '7X': 'first check',
            'A': 'first check',
            'B': 'first check',
            'C': 'first check',
            'D': 'first check',
            'E': 'first check',
            'F': 'first check',
            'FX': 'first check',
            'G': 'first check',
            'J': 'first check',
            'L': 'first check',
            'M': 'first check',
            'N': 'first check',
            'Q': 'first check',
            'R': 'first check',
            'S': 'first check',
            'SIR': 'first check',
            'W': 'first check',
            'Z': 'first check',
        }

    def mta_site_check(self, instance, tags):

        url = self.init_config.get('mta_url', "http://www.mta.info/")
        timeout = float(self.init_config.get('timeout', 5))

        start_time = time.time()

        result = hashlib.md5(url.encode())
        aggregation_key = result.hexdigest()

        try:
            self.log.debug("Connecting to MTA site at '{0}'".format(url))
            r = requests.get(url, timeout=timeout)
            end_time = time.time()
        except requests.exceptions.Timeout as e:
            # If there's a timeout, send event plus failure service check
            tags.append("status_code:{0}".format(r.status_code))
            self.timeout_event(url, timeout, aggregation_key, tags)
            self.service_check('mta_site.can_connect', 2)
            return

        tags.append("status_code:{0}".format(r.status_code))

        if r.status_code is not 200:
            self.status_code_event(url, r, aggregation_key, tags)
            # service check status = warning
            check_status = 1
        else:
            # service check status = success
            check_status = 0

        timing = end_time - start_time
        self.gauge('mta_site.response_time', timing, tags=tags)
        self.service_check('mta_site.can_connect', status=check_status)

    def status_code_event(self, url, r, aggregation_key, tags):
        self.event({
            'timestamp': int(time.time()),
            'event_type': 'mta_site_check',
            'alert_type': 'warning',
            'msg_title': 'MTA site: Invalid response code',
            'msg_text': '%s returned a status of %s' % (url, r.status_code),
            'aggregation_key': aggregation_key,
            'tags': tags
        })


    # for service check
    def _status_convertor_sc(self, status):
        status = status.lower()
        if 'not' in status:
            return 2
        else:
            self.lines_running += 1
            return 0

    # to get metric value
    def _status_convertor_metric(self, status):
        status = status.lower()
        if 'not' in status:
            return 0
        else:
            return 1

    def _status_to_tag(self, status):
        tag = "status:"
        status = status.lower().replace(" ", "_")
        tag = tag + status
        return tag

    def _get_status_link(self, line):
        line = line.replace('/', "").lower()
        to_check = line.lower()

        if to_check == "1" or to_check == "2" or to_check == "3":
            line = "123"
        elif to_check == "a" or to_check == "c" or to_check == "e":
            line = "ace"
        elif to_check == "4" or to_check == "5" or to_check == "6":
            line = "456"
        elif to_check == "b" or to_check == "d" or to_check == "f" or to_check == "m":
            line = "bdfm"
        elif to_check == "n" or to_check == "q" or to_check == "r":
            line = "nqr"

        return 'http://www.mta.info/status/subway/%s' % (line)

    def timeout_event(self, url, timeout, aggregation_key, tags):
        self.event({
            'timestamp': int(time.time()),
            'event_type': 'mta_site_check',
            'alert_type': 'error',
            'msg_title': 'MTA site: timeout',
            'msg_text': '%s timed out after %s seconds.' % (url, timeout),
            'aggregation_key': aggregation_key,
            'tags': tags
        })

    def goodservice_api_request(self):
        r = requests.get('https://goodservice.io/api/routes')
        rjson = dict(r.json())
        return rjson["routes"]

    def check(self, instance):
        self.lines_running = 0
        tags = self.init_config.get('tags', [])
        self.main()
        self.gauge('mta.lines_running', self.lines_running)
        self.mta_site_check(instance, tags)
        self.last_ping = time.time()

    def main(self):
        now = time.time()
        mta_status_page = self.init_config.get('mta_status_page', 'http://web.mta.info/status/serviceStatus.txt')
        self.log.debug("Connecting to MTA status at '{0}'".format(mta_status_page))

        mta_status_page = self.init_config.get('mta_status_page', 'http://web.mta.info/status/serviceStatus.txt')
        page = requests.get(mta_status_page)

        html_page = BeautifulSoup(page.text, 'html.parser')

        # send metric about how many seconds since last update
        last_updated = html_page.find('timestamp').text
        time_since_updated = time.mktime(time.strptime(last_updated, "%m/%d/%Y %I:%M:%S %p"))
        # account for timezone differences when making that timestamp, since it will do it according to the local system's clock. whoops. this assumes UTC - 4 aka 14400 seconds
        timezone_offset = time.timezone * 3600
        time_since_updated += timezone_offset
        # very rough calculation to accomodate for daylight savings time
        is_dst = not (time.localtime().tm_mon <= 3 and time.localtime().tm_mday <= 10) and not (
                    time.localtime().tm_mon >= 11 and time.localtime().tm_mday >= 1)
        if is_dst:
            time_since_updated += 14400
        else:
            time_since_updated += 18000

        seconds_since_updated = (now - time_since_updated)
        self.gauge('mta.time_since_status_update', seconds_since_updated)

        # lines = html_page.find_all('line')

        # create dict with value being the position that the line is in the lines index, gets around how python dict are itereated over randomly in a loop

        # query the goodservice.io API to get the status of each line
        gs_response = self.goodservice_api_request()

        for line in gs_response:
            # get the name and the status for the current line
            name = gs_response[line]["name"]
            new_status = gs_response[line]["status"]
            saved_status = self.saved_line_statuses[name]


            event_tags = ["status:{0}".format(new_status.replace(" ", "_"))]
            # check if the saved status of the lines is the same as the most recent one
            if saved_status.lower() != new_status.lower():
                self.log.debug('Updating status for {0} to {1}'.format(name, new_status))

                event_tags.append("line:{0}".format(name))

                if "not" not in new_status.lower():
                    alert = "success"
                else:
                    alert = "warning"

                self.event({
                    'timestamp': int(time.time()),
                    'event_type': 'mta_status_update',
                    'alert_type': alert,
                    'tags': event_tags,
                    'msg_title': '[MTA] {0} service update: {1}'.format(name, new_status.lower()),
                    'msg_text': '''
            The MTA has updated the service status for %s from '%s' to '%s'
            Check the status page for more information: %s
            ''' % (name, saved_status.lower(), new_status.lower(), self._get_status_link(name))
                })
                self.saved_line_statuses[name] = new_status
            else:
                self.log.debug('No update on {}'.format(name))

            # submit service checks for all lines

            line_tag = "line:{0}".format(name)

            self.service_check('mta.line_up', status=self._status_convertor_sc(new_status), tags=[line_tag])

            # use _status_convertor to find if good service(1) then send a 1 or 0 for a metric to determine uptime later on

            self.gauge('mta.line_service', value=self._status_convertor_metric(new_status),
                       tags=[line_tag, self._status_to_tag(new_status)])


