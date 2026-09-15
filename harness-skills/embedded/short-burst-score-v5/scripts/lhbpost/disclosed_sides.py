"""Observable ranked-side contributions are not actual seat net purchases."""
import math
import pandas as pd

PROTOCOL='DISCLOSED_RANKED_SIDE_CONTRIBUTIONS_V1'


def conflicting_groups(records):
    """A named seat with contradictory amounts has no identifiable additive split.

    Anonymous institution rows remain distinct reported entries, not fabricated
    identities. Different named-seat variants are retained as evidence, not summed.
    """
    observations={};bad=set()
    for row in records:
        dept=str(row.get('seat_code') or '')
        if dept in ('','0') or row.get('exalter')=='机构专用':continue
        group=(str(row['ts_code']),str(row['trade_date']),str(row['reason']))
        key=group+(dept,)
        values=observations.setdefault(key,{'buy':set(),'sell':set()})
        values[row['side']].add(float(row['disclosed_amount']))
        counterpart=row.get('counterpart_amount')
        if counterpart is not None and not pd.isna(counterpart):
            value=float(counterpart)
            if not math.isfinite(value) or value<0:raise ValueError('invalid_disclosed_counterpart_amount')
            values['sell' if row['side']=='buy' else 'buy'].add(value)
        if any(len(v)>1 for v in values.values()):bad.add(group)
    return bad


def side_records(raw_by_side):
    from .data.local_postmarket import _code
    output=[]
    for side,rows in raw_by_side.items():
        direction='buy' if side in ('top_inst_buy','BUY','buy') else 'sell' if side in ('top_inst_sell','SELL','sell') else None
        if direction is None:raise ValueError('unknown_disclosure_side')
        for i,row in enumerate(rows):
            try:code=_code(str(row['SECURITY_CODE']))
            except ValueError:continue
            amount=float(row[direction.upper()])
            if not math.isfinite(amount) or amount<0:raise ValueError('invalid_disclosed_own_side_amount')
            reason=str(row.get('EXPLANATION') or row.get('EXPLAIN') or '')
            name=str(row.get('OPERATEDEPT_NAME') or '').strip()
            if not reason or not name:raise ValueError('missing_disclosure_reason_or_name')
            category='institution' if '机构专用' in name else 'connect' if any(x in name for x in ('沪股通专用','深股通专用','港股通专用')) else 'broker'
            output.append({'ts_code':code,'trade_date':str(row['TRADE_DATE'])[:10].replace('-',''),'reason':reason,
                'side':direction,'disclosed_amount':amount,'category':category,'exalter':name,'seat_code':str(row.get('OPERATEDEPT_CODE') or ''),
                'source_report':'RPT_BILLBOARD_DAILYDETAILS'+direction.upper(),'source_row':i,
                'source_page':row.get('_source_page',1),'page_row':row.get('_source_row',i),
                'source_window_start':row.get('_source_window_start',''),'source_window_end':row.get('_source_window_end',''),
                'identity_disclosed':str(row.get('OPERATEDEPT_CODE') or '') not in ('','0') and name!='机构专用',
                'source_trade_id':row.get('TRADE_ID'),
                'counterpart_amount':row.get('SELL' if direction=='buy' else 'BUY'),
                'amount_scope':PROTOCOL,'counterpart_disclosure':'not_observable' if row.get(('SELL' if direction=='buy' else 'BUY')) is None else 'observed_in_raw_source'})
    conflicts=conflicting_groups(output)
    for row in output:
        row['group_amount_conflict']=(row['ts_code'],row['trade_date'],row['reason']) in conflicts
    return output


def attach_disclosed_contributions(events,records):
    e=events.copy();d=pd.DataFrame(records)
    if d.empty:return e
    required={'ts_code','trade_date','reason','side','disclosed_amount','category','source_report','source_row','amount_scope'}
    if not required<=set(d):raise ValueError('disclosed_sides_schema_missing')
    if not d.amount_scope.eq(PROTOCOL).all():raise ValueError('disclosed_sides_protocol_mismatch')
    if not d.side.isin(['buy','sell']).all() or not d.category.isin(['institution','broker','connect']).all():
        raise ValueError('invalid_disclosed_side_or_category')
    if not d.apply(lambda r:r.source_report=='RPT_BILLBOARD_DAILYDETAILS'+r.side.upper(),axis=1).all():
        raise ValueError('source_report_side_mismatch')
    if d.duplicated(['source_report','source_row']).any():raise ValueError('duplicate_disclosed_source_record')
    # Recompute from preserved observations; a caller cannot clear a conflict flag.
    conflicts=conflicting_groups(d.to_dict('records'))
    if 'group_amount_conflict' in d:
        for row in d.loc[d.group_amount_conflict.eq(True)].to_dict('records'):
            conflicts.add((str(row['ts_code']),str(row['trade_date']),str(row['reason'])))
    conflicts={(code,pd.Timestamp(day).normalize(),reason) for code,day,reason in conflicts}
    d['trade_date']=pd.to_datetime(d['trade_date'].astype(str));d['disclosed_amount']=pd.to_numeric(d['disclosed_amount'],errors='raise')
    if not d.disclosed_amount.map(lambda x:math.isfinite(x) and x>=0).all():raise ValueError('invalid_disclosed_amount')
    grouped=d.groupby(['ts_code','trade_date','reason'],sort=False).indices
    results=[]
    for _,event in e.iterrows():
        positions=grouped.get((event.ts_code,event.trade_date,event.rep_reason),[])
        z=d.iloc[positions]
        conflict=(str(event.ts_code),pd.Timestamp(event.trade_date).normalize(),str(event.rep_reason)) in conflicts
        complete=set(z.side)=={'buy','sell'} and not conflict
        row={'trade_date':event.trade_date,'ts_code':event.ts_code,'rep_reason':event.rep_reason,'disclosed_sides_complete':complete,
            'capital_observation_protocol':PROTOCOL,'actual_seat_net_observability':'not_observable',
            'disclosed_group_amount_conflict':conflict,
            'disclosed_group_status':'unidentifiable_conflicting_source_rows' if conflict else ('complete_ranked_sides' if complete else 'missing_side')}
        if complete:
            for category in ('institution','broker','connect'):
                for side in ('buy','sell'):
                    row[f'{category}_disclosed_{side}']=float(z.loc[z.category.eq(category)&z.side.eq(side),'disclosed_amount'].sum())
                row[f'{category}_disclosed_balance']=row[f'{category}_disclosed_buy']-row[f'{category}_disclosed_sell']
                denom=float(event.impact_denominator)
                row[f'{category}_disclosed_impact']=row[f'{category}_disclosed_balance']/denom if denom>0 else float('nan')
            buy=float(z.loc[z.side.eq('buy'),'disclosed_amount'].sum());sell=float(z.loc[z.side.eq('sell'),'disclosed_amount'].sum())
            row['disclosed_buy_sell_balance']=(buy-sell)/(buy+sell) if buy+sell>0 else 0.
            row['disclosed_buy1']=float(z.loc[z.side.eq('buy'),'disclosed_amount'].max())
        results.append(row)
    e=e.merge(pd.DataFrame(results),on=['trade_date','ts_code','rep_reason'],how='left',validate='one_to_one')
    for category in ('institution','broker','connect'):
        key=f'{category}_disclosed_impact'
        if key in e:e[key+'_pctile']=e.groupby('trade_date')[key].rank(pct=True)
    e['seat_detail_available']=e['disclosed_sides_complete'].fillna(False)
    # Do not expose actual net as zero merely because its counterpart is undisclosed.
    for key in ['inst_net','broker_net','connect_net','inst_net_buy_ratio','broker_net_buy_ratio','inst_net_impact_pctile','broker_net_impact_pctile','buy_sell_balance']:
        e[key]=float('nan')
    return e
