#!/bin/bash

BRANCH=`git branch --no-color 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/\1/'`

if [ "$BRANCH" != "master" ] && [ "$BRANCH" != "staging" ]
then
    echo "I don't know how to deploy branch '${BRANCH}' - only 'staging' and 'master'"
    exit
fi

if [ "$BRANCH" == "master" ]
then
    read -n 1 -p "Really deploy branch '${BRANCH}' to production? " CONFIRM
    if [ "$CONFIRM" != "y" ]
    then
        echo
        exit
    fi
    echo
fi

echo "Compiling .less files"
for i in static/*less ; do lessc $i ; done

echo "Uploading branch '${BRANCH}' to App Engine"
appcfg.py update . --version $BRANCH
