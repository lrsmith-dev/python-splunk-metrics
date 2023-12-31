#!/bin/env python

import json
import argparse

from datetime import datetime
import splunklib.client as client
from splunklib.results import JSONResultsReader

################################################################################

splunk_searches = {
    "index_size_bytes" : 'index=_internal source=*license_usage.log type="Usage" splunk_server=* earliest=-7d@d | eval Date=strftime(_time, "%Y/%m/%d") | eventstats sum(b) as volume by idx, Date | eval B=round(volume,5)| timechart limit=0 span=1h first(B) AS volume by idx',
    "test"             : 'index=_internal source=*license_usage.log type="Usage" splunk_server=* earliest=-7d@d | eval Date=strftime(_time, "%Y/%m/%d") | eventstats sum(b) as volume by idx, Date | eval B=round(volume,5)| timechart limit=0 span=1h first(B) AS volume by idx',
}

################################################################################

## Entry point of the lambda
def lambda_handler(event, context):
    message = 'Hello {} {}!'.format(event['first_name'], event['last_name'])
    return {
        'message' : message
    }


def executeSplunkSearch(service, splunk_search):

    resultDict = {}

    # TODO : Wrap in try and skip any with errors. 
    response = service.jobs.oneshot('search ' + splunk_search, output_mode="json")

    reader = JSONResultsReader(response)
    for result in reader:
        if isinstance(result, dict):
            del result["_span"] 
            time = (datetime.strptime(result.pop("_time"), '%Y-%m-%dT%H:00:00.000+00:00').date()).strftime('%s')
            if result:
              resultDict[time] = result

    return resultDict


# Run the specified Splunk Search
def runSplunkSearch(splunk_server, splunk_user="admin", splunk_password="password", searches=None):

    metricDict = {}

    service = client.connect(host=splunk_server, port=8089,
                   username=splunk_user, password=splunk_password)
    assert isinstance(service, client.Service)

    if searches is None:
        #print("DEBUG: Executing all splunk searches")
        for search in splunk_searches:
          #print("DEBUG: Executing splunk search " + search)
          metricDict[search] = executeSplunkSearch(service,splunk_searches[search])
    else:
        # TODO : Assume is comma separate list of all searches to run.
        #print("DEBUG: Executing specified splunk search")
        for search in searches.split(','):
          metricDict[search] = executeSplunkSearch(service,splunk_searches[search])

    return metricDict 

def parseArgs():
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-s", "--splunk-server", help="Splunk Server",default='localhost')
    argParser.add_argument("--metric-format", help="Metric Format",default='wavefront')
    argParser.add_argument("-o","--output", help="Output")

    return argParser.parse_args()


################################################################################


if __name__ == "__main__":

    args = parseArgs()
    #print("args=%s" % args)

    #metrics = runSplunkSearch(args.splunk_server,searches="index_size_bytes")
    #metrics = runSplunkSearch(args.splunk_server,searches="index_size_bytes,test")
    metrics = runSplunkSearch(args.splunk_server)
    for key,value in metrics.items():
        print(key + " : " + str(value) )