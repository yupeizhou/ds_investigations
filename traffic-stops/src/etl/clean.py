

import pandas as pd
import numpy as np
import os

basedir = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(basedir, '..', '..', 'data')

# ---------------------------------------------------------------------
# Cleaning single columns
# ---------------------------------------------------------------------


def clean_timestamp(stops):
    '''convert to timestamp; round to nearest 5 minutes.'''
    stops = stops.assign(timestamp=pd.to_datetime(stops['timestamp']))

    ns5min = 5*60*1000000000 # 5 minutes in ns
    ts = (stops.timestamp.astype(np.int64).where(lambda x: x > 0) // ns5min + 1) * ns5min
    return pd.to_datetime(ts)


def clean_stop_cause(stops):
    '''clean to equipment and moving violations'''

    to_keep = ['Moving Violation', 'Equipment Violation']
    is_viol = stops.stop_cause.isin(to_keep)
    return stops.stop_cause.where(is_viol)


def clean_service_area(stops):
    '''clean service area'''

    replaced = stops['service_area'].replace({'Unknown': np.NaN})
    return replaced


def clean_subject_age(stops):
    '''clean subject age'''

    # non-digites to NaN
    ages = pd.to_numeric(stops.subject_age, errors='coerce')
    # outliers to NaN
    ages = ages.where((ages >= 15) | (ages < 100))
    # round ages to nearest 5 years
    ages = (ages / 5).round() * 5

    return ages


def clean_subject_sex(stops):
    '''clean subject sex'''

    return stops.subject_sex.replace(regex={'M': 1, 'F': 0, '[^MF]': np.NaN})


def clean_yes_no(colname):
    '''clean yes/no columns'''

    def closure(stops):
        out = stops[colname].replace(regex={'Y|y': 1, 'N|n': 0})
        return out.where((out == 0) | (out == 1))

    return closure


# ---------------------------------------------------------------------
# main cleaning logic
# ---------------------------------------------------------------------

def main():
    
    url = 'http://seshat.datasd.org/pd/vehicle_stops_2016_datasd.csv'
    outpath = os.path.join(OUTDIR, 'cleaned_stops.csv')
    stops = pd.read_csv(url)

    clean_dict = {}
    for c in stops.columns:
        func = 'clean_%s' % c
        if func in globals():
            clean_dict[c] = globals()[func]

    yn_cols = ['sd_resident', 'arrested', 'searched', 
               'obtained_consent', 'contraband_found', 'property_seized']

    for c in yn_cols:
        clean_dict[c] = clean_yes_no(c)

    (
        stops
        .reset_index()
        .rename(columns={'index': 'id'})
        .assign(**clean_dict)
        .drop(['stop_date', 'stop_time'], axis=1)
        .to_csv(outpath, index=False)
    )

    return


if __name__ == '__main__':
    main()
            
                
