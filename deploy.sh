#!/bin/bash

# Check that all dependencies are available:
dependencies='git sed lessc appcfg.py'
for binary in $dependencies; do
    if [ -z `which $binary` ]; then
        echo "Required binary '$binary' was not found in \$PATH:"
        echo $PATH
        exit
    fi
done

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

echo "Generating version.txt"
git rev-parse --verify HEAD > version.txt

echo "Uploading branch '${BRANCH}' to App Engine"
appcfg.py update . --version $BRANCH
