#!/bin/bash

set -x

# We should ge the following variables from the environment (injected into container):
#    KML_API_BASE
#    KML_DEPL_ID
#    ZMQ_HOST
#    ZMQ_PORT
#	 MY_POD_IP
#
# Sample Usage:
#    ./local-test-run-dep-mgr.sh http://{host_ip}:9187/kml {dep_id} {host_ip} 9002 {host_ip}


echo "----------------------------------------"
echo "Running deployment manager with environment variables:"
echo "   KML_API_BASE = $KML_API_BASE"
echo "   KML_DEPL_ID = $KML_DEPL_ID"
echo "   ZMQ_HOST = $ZMQ_HOST"
echo "   ZMQ_PORT = $ZMQ_PORT"
echo "   MY_POD_IP = $MY_POD_IP"
echo "----------------------------------------"
echo ""

while true; do
    echo "run-dep-mgr -- INFO -- (re)starting Deployment manager"

    python depmgr.py \
        --model-dep-id $KML_DEPL_ID \
        --kml-api-base $KML_API_BASE \
        --zmq-host $ZMQ_HOST \
        --zmq-port $ZMQ_PORT \
        --dep-mgr-ip $MY_POD_IP 2>&1

    echo "run-dep-mgr -- WARNING -- Deployment manager terminated"
done

echo "run-dep-mgr -- ERROR -- Exiting shell"
