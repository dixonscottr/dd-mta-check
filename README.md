# dd-mta-check
Originally done for Datadog agent version 5 but now being updated for the latest version of the agent.
- This was designed as a custom DD integration to pull stats on NYC subway (Developed for Agent 5)

![](https://imgix.datadoghq.com/img/blog/monitor-mta-status/mta-service-dash.png)

**Instructions for the agent on Linux**
1. Place `mta_check.yaml` in `/etc/datadog-agent/conf.d/` and `mta_check.py` in `/etc/datadog-agent/checks.d/`
2. Install [beautiful soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) in Agent's Python environment (`sudo -H /opt/datadog-agent/embedded/bin/pip install bs4`) 
3. [Restart agent](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#restart-the-agent) (`sudo service datadog-agent restart`)

## References

- [How to write an agent check](https://docs.datadoghq.com/developers/custom_checks/write_agent_check/)
- [Monitoring the NYC subway system with Datadog](https://www.datadoghq.com/blog/monitor-mta-status/)
