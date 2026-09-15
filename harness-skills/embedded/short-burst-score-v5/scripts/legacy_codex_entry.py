"""Internal child entry, protected by the canonical execution environment."""
import json
import os

def main():
    if os.environ.get('CODEX_STOCK_CANONICAL_EXECUTION') != '1' or os.environ.get('ONESTOCK_STOCK_CANONICAL_CHILD') != '1':
        print(json.dumps({'status':'BLOCKED','errors':['canonical_stock_legacy_entry_direct_execution_blocked']}))
        return 2
    from local_business import main as run
    return run()

if __name__ == '__main__':
    raise SystemExit(main())
