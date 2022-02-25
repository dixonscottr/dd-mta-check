import time
import requests



from bs4 import BeautifulSoup

from checks import AgentCheck
from hashlib import md5

class MTACheck(AgentCheck):

    def __init__(self, name, init_config, agentConfig, instances=None):
        AgentCheck.__init__(self, name, init_config, agentConfig, instances=instances)
        self.lines_running = 0
        self.last_ping = time.time()
        self.saved_line_statuses = {
          'onetwothree_line': 'first check',
          'fourfivesix_line': 'first check',
          'seven_line': 'first check',
          'ace_line': 'first check',
          'bdfm_line': 'first check',
          'g_line': 'first check',
          'jz_line': 'first check',
          'l_line': 'first check',
          'nqr_line': 'first check',
          'shuttle_line': 'first check',
          'sir_line': 'first check'
        }

    def mta_site_check(self, instance, tags):

      url = self.init_config.get('mta_url', "http://www.mta.info/")
      timeout = float(self.init_config.get('timeout', 5))

      start_time = time.time()

      aggregation_key = md5(url).hexdigest()

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

    def _find_line_name(self, title):
      # onetwothree_status
      idx = title.find('_line')
      name = title[:idx]

      if 'one' in name:
        name = '1/2/3'
      elif 'four' in name:
        name = '4/5/6'
      elif name == 'seven':
        name = '7'
      elif name == 'sir':
        name = name.upper()
      elif name == 'ace' or name == 'bdfm' or name == 'nqr' or name == 'jz':
        name = name.upper().replace("", "/")[1: -1]
      else:
        name = name.capitalize()

      return name

    # for service check
    def _status_convertor_sc(self, status):
      status = status.lower()
      if 'good' in status:
        self.lines_running += 1
        return 0
      else:
        return 2

    # to get metric value
    def _status_convertor_metric(self, status):
      status = status.lower()
      if 'good' in status:
        return 1
      else:
        return 0

    def _status_to_tag(self, status):
      tag = "status:"
      status = status.lower().replace(" ", "_")
      tag = tag + status
      return tag

    def _get_status_link(self, line):
      line = line.replace('/', "").lower()

      if line.lower() == 'shuttle':
        line = 's'

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


    def check(self, instance):
        self.lines_running = 0
        tags = self.init_config.get('tags', [])
        self.web_scraper()
        self.gauge('mta.lines_running', self.lines_running)
        self.mta_site_check(instance, tags)
        self.last_ping = time.time()

    def web_scraper(self):
      now = time.time()
      mta_status_page = self.init_config.get('mta_status_page', 'http://web.mta.info/status/serviceStatus.txt')
      self.log.debug("Connecting to MTA status at '{0}'".format(mta_status_page))
      page = requests.get(mta_status_page)

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
      is_dst = not(time.localtime().tm_mon <= 3 and time.localtime().tm_mday <= 10) and not(time.localtime().tm_mon >= 11 and time.localtime().tm_mday >= 1)
      if is_dst:
        time_since_updated += 14400
      else:
        time_since_updated += 18000

      seconds_since_updated = (now - time_since_updated)
      self.gauge('mta.time_since_status_update', seconds_since_updated)


      lines = html_page.find_all('line')

      # create dict with value being the position that the line is in the lines index, gets around how python dict are itereated over randomly in a loop
      new_line_statuses = {
        'onetwothree_line': 0,
        'fourfivesix_line': 1,
        'seven_line': 2,
        'ace_line': 3,
        'bdfm_line': 4,
        'g_line': 5,
        'jz_line': 6,
        'l_line': 7,
        'nqr_line': 8,
        'shuttle_line': 9,
        'sir_line': 10
      }
      # update new_line_statuses with new statuses from the update
      for line, status in new_line_statuses.items():
        idx = status
        new_line_statuses[line] = lines[idx].contents[3].text

      for line, saved_status in self.saved_line_statuses.iteritems():

        # new_status = locals()[line] # uses function's local variables
        new_status = new_line_statuses[line]
        line_name = self._find_line_name(line)

        event_tags=["status:{0}".format(new_status.replace(" ", "_"))]

        # check if the saved status of the lines is the same as the most recent one
        if saved_status.lower() != new_status.lower():
          self.log.debug('Updating status for {0} to {1}'.format(line, new_status))


          event_tags.append("line:{0}".format(line_name))

          if "good" not in new_status.lower():
            alert = "warning"
          else:
            alert="success"

          self.event({
            'timestamp': int(time.time()),
            'event_type': 'mta_status_update',
            'alert_type': alert,
            'tags': event_tags,
            'msg_title': '[MTA] {0} service update: {1}'.format(line_name, new_status.lower()),
            'msg_text': '''
            The MTA has updated the service status for %s from '%s' to '%s'
            Check the status page for more information: %s
            ''' % (line_name, saved_status.lower(), new_status.lower(), self._get_status_link(line_name))
          })
          self.saved_line_statuses[line] = new_status
        else:
          self.log.debug('No update on {}'.format(line))

        # submit service checks for all lines

        line_tag = "line:{0}".format(line_name)

        self.service_check('mta.line_up', status=self._status_convertor_sc(new_status), tags=[line_tag])

        # use _status_convertor to find if good service(1) then send a 1 or 0 for a metric to determine uptime later on

        self.gauge('mta.line_service', value=self._status_convertor_metric(new_status), tags=[line_tag, self._status_to_tag(new_status)])
