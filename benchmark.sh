#!/usr/bin/env bash

# update auth token 
# source ~/csi-marconi/tsungrc

# check if the variables have been set properly
if [[ -z "$TENANT_ID" ]] || [[ -z "$AUTH_TOKEN" ]] || [ "$TENANT_ID" = "tenant_id" ] || [ "$AUTH_TOKEN" = "auth_token" ]
then
    echo "Please use valid TENANT_ID and AUTH_TOKEN or update them in tsungrc"
fi

# Replace all auth tokens, with a valid auth token. (This is intentionally manual, to avoid accidentally stressing the production auth.)
sed -i "s/.*;/${AUTH_TOKEN};/g" ~/.tsung/auth.csv

# Create queues with the names in ~/.tsung/existingqueue.csv, if your account doesn't have them already.
python ~/csi-marconi/create_queues.py ${TENANT_ID} ${AUTH_TOKEN}

# remove previous generated tsung log fies
rm -rf /root/.tsung/log/*

# Start tsung in the controller with 'tsung start'
tsung start

# After the test is complete, cd to the logs directory generated by the tests in the controller machine.
# cd /root/.tsung/log/*
# Generate html reports with '/usr/lib/tsung/bin/tsung_stats.pl'
# /usr/local/lib/tsung/bin/tsung_stats.pl
# You can run a simple web server to view reports, with 'python -m SimpleHTTPServer'
# Enjoy your performance reports!!
