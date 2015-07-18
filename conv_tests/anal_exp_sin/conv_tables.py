
import sys
import json
import csv
import math
import os

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    import matplotlib.path as mpath
    import numpy

    HAVE_MATPLOTLIB=True
    def make_table_plot( title, table, n_h, n_d):
        if not HAVE_MATPLOTLIB: return
        
        colors = plt.cm.Dark2(numpy.linspace(0, 1, 12))
        #colors = ['yellowgreen', 'gold', 'lightskyblue', 'lightcoral', 'red', 'blue', 'gray']
        plt.hold(False)
        legend_plot_list=[]
        legend_label_list=[]
        for _ih in range(0,n_h):
            x_vals=[]
            y_vals=[]
            i_col = 2*_ih + 1
            for _id in range(0,n_d):
                i_row = _id + 2
                x_vals+=[ table[i_row][0] ]
                y_vals+=[ table[i_row][i_col] ]
                
            plot=plt.loglog(x_vals, y_vals, 'o-', color=colors[_ih])
            legend_label_list += [ str(table[1][i_col]) ]
            legend_plot_list += [ plot[0] ]        
            plt.hold(True)
        
        Path = mpath.Path
        path_data = [
            (Path.MOVETO, (0, 1)),
            (Path.LINETO, (1, 1)),
            (Path.LINETO, (0,0.5)),
            (Path.CLOSEPOLY, (0, 1)),
            ]
        codes, verts = zip(*path_data)
        path = mpath.Path(verts, codes)
        x, y = zip(*path.vertices)
        plt.plot(x, y, 'go-')
        
        plt.title(title)
        plt.xlabel('fracture span')
        plt.ylabel('norm of error')
        plt.legend(legend_plot_list, legend_label_list)
        plt.grid(True)
        pp = PdfPages(title+".pdf")
        plt.savefig(pp, format='pdf')
        pp.close()
        plt.hold(False)

except ImportError:
    def make_table_plot(title, table, n_h, n_d):
        pass
    HAVE_MATPLOTLIB=False



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
        #print case
        i_row = case["id_frac"] + 2
        i_col = 2*case["ih"] + 1
        table[1][i_col] = case["h"]
        table[i_row][0] = case["d_frac"]
        table[i_row][i_col] = value
    
    # conv order estimate between lines
    for id in range(1, n_d):
        for ih in range(0, n_h):
            i_row=id+2
            i_col=2*ih + 1
            #print table[i_row][0] , table[i_row-1][0], table[i_row][i_col] , table[i_row-1][i_col]
            try:
                d_ratio = table[i_row][0] / table[i_row-1][0]
                value_ratio = table[i_row][i_col] / table[i_row-1][i_col]
                table[i_row][i_col+1]=math.log( value_ratio )/ math.log( d_ratio )
            except (ValueError, ZeroDivisionError):
                pass
    
    # conv order estimate statistic
    
    # make plot of the table columns (no conv order estimates)
    make_table_plot(table_name, table, n_h, n_d)
    #print table
    return table

def make_table(cases_results):
    """
    Accepts list of tuples (case, norm_value).
    Form a tables, see make table ...
    :type cases_results: list of tuples
    """
    # make list of data for every norm
    norms_dict = {}
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
    with open(csv_file, "wb") as f:
        csv_out=csv.writer(f)
        items = tables_dict.items()
        items.sort()
        for key, table in items:
            for row in table:
                csv_out.writerow(row)
            csv_out.writerow([])    


def colect_norms(all_norms):
    norms_list = []
    for dir_path, dir_list, file_list in os.walk("."):
        for fname in file_list:
            if (fname == "norms_raw.json"):
                with open(os.path.join(dir_path, fname), "r") as f:
                    (case, norms)=json.load(f)
                    if case['d_frac'] < 0.11:
                        case['id_frac']+=1
                        if 'reference_case' in case:
                            case['reference_case']['id_frac']+=1
                    norms_list.append( (case, norms) )
    with open(all_norms, "w") as f:
        json.dump(norms_list, f)



  
def main():
    all_norms_file='norms_all.json'
    if not os.path.isfile(all_norms_file):
        colect_norms(all_norms_file)

    with open(all_norms_file, "r") as f:
        norms_list = json.load(f)

    tables_dict=make_table( norms_list )
    #for key, table in tables_dict.iteritems():
    #    make_graph(key, table)
    write_tables(tables_dict, "norms_table.csv")

        
        
if __name__ == "__main__":
   main()
