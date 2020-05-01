#!/bin/bash

x=1
while [ $x -le 100000 ]
do
	curl -v -X POST --data "city=Montreal" 0.0.0.0:32827
	x=$(( $x + 1 ))
done
