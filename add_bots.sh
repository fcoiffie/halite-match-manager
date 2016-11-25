#!/bin/bash
for i in bots/*
do
   botname=${i/bots\//}
  ./manager.py -A "$botname" -p "$i"/MyBot.native
done
