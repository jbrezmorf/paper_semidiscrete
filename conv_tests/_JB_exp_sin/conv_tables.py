
import sys
import json
import csv
import math

def single_table(table_name, values):
    """
    Get values in form of list of  (case, value), form table (list of rows):
    name, ....
    -   , h1,   -  ,    h2, ...
    d1  , norm, eoc,
    ...
    """
    n_h=max([ item[0]["ih"] for item in values ])+1
    n_d=max([ item[0]["id_frac"] for item in values ]) +1
    n_cols=2*n_h + 1 # first column are d_frac values
    n_rows=n_d + 2   # first line is table name, secodn h values
    table = [[0] * n_cols for i in range(n_rows)]
    table[0][0] = table_name
    for  case, value in values:
        i_row = case["id_frac"] + 2
        i_col = 2*case["ih"] + 1
        table[1][i_col] = case["h"]
        table[i_row][0] = case["d_frac"]
        table[i_row][i_col] = value
    for id in range(1, n_d):
        for ih in range(0, n_h):
            i_row=id+2
            i_col=2*ih + 1
            table[i_row][i_col+1]=\
                math.log( table[i_row][i_col] / table[i_row-1][i_col] )\
                / math.log( table[i_row][0] / table[i_row-1][0] )
    return table

def make_table(cases_results):
    """
    Accepts list of tuples (case, norm_value).
    Form a tables, see make table ...
    :type cases_results: list of tuples
    """
    # make list of data for every norm
    norms_dict={}
    for case, norms in cases_results:
        for key, value in norms.items():
            norms_dict.setdefault(key, [])
            norms_dict[key].append( (case, value) )

    # format tables, ih as inner index
    # compute estimate of order convergence according to d_frac
    for key, norm in norms_dict.iteritems():
        norms_dict[key] = single_table(key, norm)

    return norms_dict

def write_tables(tables_dict, csv_file):
    with open(csv_file, "wb") as f
        csv_out=csv.writer(f)
        items = tables_dict.items()
        items.sort()
        for key, table in items:
            for row in table:
                csv_out.writerow(row)


def main(): 
    json_file = sys.argv[1]
    with open(json_file, "r") as f:
        tables_dict=make_table( json.load(f) )
    write_tables(tables_dict, "norms_table.csv")

        
        
if __name__ == "__main__":
   main()
