# dd-mta-check
Custom DD integration to pull stats on NYC subway (Developed for Agent 5)

**Instructions for Agent 5 on Linux**
1. Place `mta_check.yaml` in `/etc/dd-agent/conf.d/` and `mta_check.py` in `/etc/dd-agent/checks.d/`
2. Install [beautiful soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) in Agent's Python environment (`sudo -H /opt/datadog-agent/embedded/bin/pip install bs4`) 
3. [Restart agent](https://docs.datadoghq.com/agent/basic_agent_usage/amazonlinux/?tab=agentv5#commands) (`sudo service datadog-agent restart`)

## References

- [How to write an agent check](https://docs.datadoghq.com/developers/custom_checks/write_agent_check/)
