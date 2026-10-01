"""本机唯一公共入口：委托已登记的股票统一运行器。"""
import os
from pathlib import Path
import sys
APP_ROOT=Path(__file__).resolve().parents[4]
APP_SCRIPTS=APP_ROOT/'scripts'
if str(APP_SCRIPTS) not in sys.path:sys.path.insert(0,str(APP_SCRIPTS))
from tdx_path_config import resolve_data_root
HOME=APP_ROOT
sys.dont_write_bytecode=True
os.environ['PYTHONDONTWRITEBYTECODE']='1'
os.environ['PYTHONUTF8']='1'
os.environ['PYTHONIOENCODING']='utf-8'
os.environ.setdefault('ONESTOCK_STOCK_DATA_ROOT',str(resolve_data_root()/'business_data'/'a-share-short-burst-score'))
os.environ['PYTHONPATH']=str(APP_SCRIPTS)+(os.pathsep+os.environ['PYTHONPATH'] if os.environ.get('PYTHONPATH') else '')
from stock_canonical_runtime import facade_main
if __name__=='__main__': raise SystemExit(facade_main(__file__))
