#!/bin/bash

version="0.6"
zipName="plugin.video.yogaglo-$version.zip"
xbmc_plugin_name="plugin.video.yogaglo"

zip -r $zipName $xbmc_plugin_name -x=*.git* -x=*.pyc -x=*.settings* -x=*test* -x=*.org* -x=*.bash* -x=*.project* -x=*.pydevproject* -x=*nose2.cfg*
