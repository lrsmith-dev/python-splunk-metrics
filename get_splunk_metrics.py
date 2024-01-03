#!/bin/env python

import argparse
import json
import os

from datetime import datetime
from splunklib.results import JSONResultsReader
import splunklib.client as client

################################################################################

# Note : Later part of the code makes assumptions on the stats command. "value" is the metric value, _time will be used to get the timestamp
# the the remaining fields will be turned into k/v pair

metrics = {
    "index.size.bytes" : {
        "search": 'index=_internal source=*license_usage.log type="Usage" earliest=-1d@d | bucket _time span=1h | rename idx as index | stats sum(b) as value by _time,index' 
    },
}

class MetricPoint:

  def __init__(self, name, timestamp, value, tags):
    self.name = name
    self.timestamp = timestamp
    self.value = value
    self.tags = tags
    self.format = "opentsdb"

  # Print out the metric. Opentsdb is the default
  def __str__(self):
    tagString = ""
    for k,v in self.tags.items():
        tagString += f" {k}={v}"
    return f"{self.name} {self.timestamp} {self.value}{tagString}"



################################################################################

## Entry point of the lambda
def lambda_handler(event, context):
    message = 'Hello {} {}!'.format(event['first_name'], event['last_name'])
    return {
        'message' : message
    }

def executeSplunkSearch(service, splunk_search, host):

    resultList = []

    # TODO : Wrap in try and skip any with errors. 
    response = service.jobs.oneshot('search ' + metrics[splunk_search]['search'] , output_mode="json")
    reader = JSONResultsReader(response)
    for result in reader:
        if isinstance(result, dict):
           timestamp = (datetime.strptime(result.pop("_time"), '%Y-%m-%dT%H:%M:%S.%f+00:00').date()).strftime('%s')
           name = splunk_search
           value = result.pop('value')
           result['host'] = host
           resultList.append(MetricPoint(name,timestamp,value,result))
    return resultList


# Run the specified Splunk Search
def runSplunkSearch(splunk_server, splunk_user=None, splunk_password=None, splunk_token=None, searches=None):

    metricList = []

    if splunk_token is not None:
      #print("DEBUG : Authenticating with Splunk Token")
      service = client.connect(host=splunk_server, port=8089,
                     splunkToken=splunk_token)
    else:
      print("DEBUG : Authenticating with Splunk username/password")
      service = client.connect(host=splunk_server, port=8089,
                     username=splunk_user, password=splunk_password)
    assert isinstance(service, client.Service)

    if searches is None:
        #print("DEBUG: Executing all splunk searches")
        for search in metrics:
          #print("DEBUG: Executing splunk search " + search)
          metricList += executeSplunkSearch(service,search,splunk_server)
    else:
        #print("DEBUG: Executing specified splunk search")
        for search in searches.split(','):
          #print("DEBUG: Executing splunk search " + search)
          metricList += executeSplunkSearch(service,search,splunk_server)

    return metricList 

def parseArgs():
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-s", "--splunk-server",   help="Splunk Server",              default='localhost')
    argParser.add_argument("-u", "--splunk-user",     help="Splunk User",                default=None)
    argParser.add_argument("-p", "--splunk-password", help="Splunk Password",            default=None) 
    argParser.add_argument("-t", "--splunk-token",    help="Splunk Token",               default=None) 
    argParser.add_argument(      "--metric-format",   help="Metric Format",              default='wavefront')
    argParser.add_argument(      "--metric-prefix",   help="Prefix to append to metric", default=None)
    argParser.add_argument("-o", "--output",          help="Output",                     default=None )

    return argParser.parse_args()

def overrideArgsWithEnvVariables(args):

    args.splunk_server   = os.getenv('SPLUNK_SERVER',   args.splunk_server)
    args.splunk_user     = os.getenv('SPLUNK_USER',     args.splunk_user)
    args.splunk_password = os.getenv('SPLUNK_PASSWORD', args.splunk_password)
    args.splunk_token    = os.getenv('SPLUNK_TOKEN',    args.splunk_token)


################################################################################

if __name__ == "__main__":

    args = parseArgs()                  #print("args=%s" % args)
    overrideArgsWithEnvVariables(args)  #print("args=%s" % args)

    metrics = runSplunkSearch(args.splunk_server,args.splunk_user,args.splunk_password,args.splunk_token)
    for metric in metrics:
       print(metric)