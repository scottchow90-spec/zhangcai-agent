"""本机唯一公共入口：委托已登记的股票统一运行器。"""
import os
from pathlib import Path
import sys
HOME=Path(r"F:\Codex\Home")
DEPENDENCIES=HOME/'runtime-deps'/'a-share-short-burst-score'
sys.dont_write_bytecode=True
os.environ['PYTHONDONTWRITEBYTECODE']='1'
os.environ['PYTHONUTF8']='1'
os.environ['PYTHONIOENCODING']='utf-8'
os.environ['ONESTOCK_STOCK_DATA_ROOT']=str(HOME/'business_data'/'a-share-short-burst-score')
os.environ['PYTHONPATH']=str(DEPENDENCIES)+(os.pathsep+os.environ['PYTHONPATH'] if os.environ.get('PYTHONPATH') else '')
sys.path.insert(0,str(DEPENDENCIES));sys.path.insert(0,str(HOME/'scripts'))
from stock_canonical_runtime import facade_main
if __name__=='__main__': raise SystemExit(facade_main(__file__))
