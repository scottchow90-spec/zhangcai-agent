#!/usr/bin/env python3
from __future__ import annotations
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from lhbpost.research import build_model

def main():
    p=argparse.ArgumentParser(description='构建盘后龙虎榜历史滚动样本外统计模型（V5.0）')
    p.add_argument('--events',required=True);p.add_argument('--cutoff',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();m=build_model(a.events,a.cutoff,a.output)
    print(a.output);print('validation_scheme=',m['validation_scheme']);print('production_qualified=',m['production_qualified']);print('acceptance=',m['acceptance'])
if __name__=='__main__':main()
