#!/usr/bin/env python3
"""
穷举扫描器 — 数据声明的硬验证
任何关于 E 盘通达信本地数据是否存在的结论，必须先过此脚本
输出: 完整的文件清单JSON，禁止跳过任何目录
"""
import os, json, sys

ROOT = r'C:\new_tdx_mock'
DATA_EXTENSIONS = {'.day', '.lc5', '.lc1', '.lc', '.~~~day', '.tcu', '.tfz', '.th2', '.tnf'}

def scan_all():
    result = {
        'root': ROOT,
        'total_files': 0,
        'total_size_mb': 0,
        'by_extension': {},
        'by_directory': {},
        'data_directories': {}
    }
    
    for dp, dn, fn in os.walk(ROOT):
        rel = os.path.relpath(dp, ROOT)
        dir_files = []
        dir_size = 0
        dir_exts = {}
        
        for f in fn:
            path = os.path.join(dp, f)
            sz = os.path.getsize(path)
            ext = os.path.splitext(f)[1].lower()
            
            result['total_files'] += 1
            result['total_size_mb'] += sz
            result['by_extension'][ext] = result['by_extension'].get(ext, 0) + 1
            
            dir_files.append(f)
            dir_size += sz
            dir_exts[ext] = dir_exts.get(ext, 0) + 1
        
        if dir_files:
            result['by_directory'][rel] = {
                'file_count': len(dir_files),
                'size_mb': round(dir_size / 1048576, 2),
                'extensions': dict(sorted(dir_exts.items()))
            }
            
            # Track data directories separately
            data_files = [f for f in dir_files if os.path.splitext(f)[1].lower() in DATA_EXTENSIONS]
            if data_files:
                result['data_directories'][rel] = {
                    'file_count': len(data_files),
                    'sample_files': list(sorted(data_files)[:5])
                }
    
    result['total_size_mb'] = round(result['total_size_mb'] / 1048576, 2)
    result['by_extension'] = dict(sorted(result['by_extension'].items(), key=lambda x: -x[1]))
    
    # Summary of data types found
    result['data_summary'] = {
        '每日K线(.day)': result['by_extension'].get('.day', 0),
        '分钟K线(.lc5)': result['by_extension'].get('.lc5', 0),
        '1分钟K线(.lc1)': result['by_extension'].get('.lc1', 0),
        '分时缓存(.tcu/.tfz/.th2/.tnf)': sum(
            result['by_extension'].get(e, 0) for e in ['.tcu', '.tfz', '.th2', '.tnf']
        ),
        '临时K线(.~~~day)': result['by_extension'].get('.~~~day', 0),
    }
    
    return result

if __name__ == "__main__" and os.environ.get(
    "ONESTOCK_STOCK_CANONICAL_CHILD"
) != "1":
    print(
        "canonical_stock_legacy_entry_direct_execution_blocked",
        file=sys.stderr,
    )
    raise SystemExit(2)


if __name__ == '__main__':
    data = scan_all()
    print(json.dumps(data, ensure_ascii=False, indent=2))
