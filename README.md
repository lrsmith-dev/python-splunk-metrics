# python-splunk-metrics
Python code that can be run standalone, as a lambda, or Splunk App to collect and forward metrics.

# Developement Setup

## Splunk Docker Setup

Local development was done leveraging the Splunk Docker Image.

1. `docker run -d  -p 8089:8089 -p 8000:8000 -e "SPLUNK_START_ARGS=--accept-license" -e "SPLUNK_PASSWORD=password" --name splunk splunk/splunk:latest`

## Python Setup

1. `python3 -m venv env`
2. `source env/bin/activate`
3. `pip3 install splunk-sdk`                # Install Splunk Python SDK
4. `pip3 install wavefront-sdk-python`      # Install Wavefront Python SDK. Does not install/compile

## VMWareVMware Aria Operations for Applications 

Previously known as Wavefront, https://tanzu.vmware.com/observability-trial
This requiers signing up for a VMWare Cloud account and a free 30 day trial.

