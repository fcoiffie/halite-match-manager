#!/bin/bash
for i in bots/*
do
   botname=${i/bots\//}
  ./manager.py -a "$botname" -p "$i"/MyBot.native
done
