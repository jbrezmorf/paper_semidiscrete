
import sys
import json
import csv
import math
import os

try:
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    import matplotlib.colors as mpl_colors
    from matplotlib.backends.backend_pdf import PdfPages
    import matplotlib.path as mpath
    import numpy
    from matplotlib import rc   
    
    rc('font',**{'family':'serif','serif':['Palatino']})
    rc('text', usetex=True)
    HAVE_MATPLOTLIB=True
    
    def make_table_plot( title, table, n_h, n_d):
        if not HAVE_MATPLOTLIB: return None
        try:
            case_idx = ['dx_dx_p_diff_exact_L2', 'dx_dx_p_diff_exact_Linf'].index(title)
        except:
            return None
        
        plot_style=['o-', '^-'][case_idx]
        value_range=mpl_colors.Normalize(0, n_h-1)
        colors=[ cm.ScalarMappable(value_range, cm.autumn), cm.ScalarMappable(value_range, cm.winter)][case_idx]                    
        legend_label=[ r'$L^2,\ ', r'$L^\infty,\ '][case_idx]
        
        #colors = ['yellowgreen', 'gold', 'lightskyblue', 'lightcoral', 'red', 'blue', 'gray']
        #plt.hold(False)
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
                
            plot=plt.loglog(x_vals, y_vals, plot_style, color=colors.to_rgba(_ih) )
            legend_label_list += [ legend_label + str(table[1][i_col]) + r'$' ]
            legend_plot_list += [ plot[0] ]        
            #plt.hold(True)
          
        #Path = mpath.Path
        #path_data = [
        #    (Path.MOVETO, (0, 1)),
        #    (Path.LINETO, (1, 1)),
        #    (Path.LINETO, (0,0.5)),
        #    (Path.CLOSEPOLY, (0, 1)),
        #    ]
        #codes, verts = zip(*path_data)
        #path = mpath.Path(verts, codes)
        #x, y = zip(*path.vertices)
        #plt.plot(x, y, 'go-')
        return (legend_plot_list, legend_label_list)

except ImportError:
    def make_table_plot(title, table, n_h, n_d):
        pass
    HAVE_MATPLOTLIB=True



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
    print "rows:", n_cols, "cols:",  n_rows
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
    
    plot = make_table_plot(table_name, table, n_h, n_d)
    #print table
    return (table, plot)

def make_table(cases_results):
    """
    Accepts list of tuples (case, norm_value).
    Form a tables, see make table ...
    :type cases_results: list of tuples
    """
    # make list of data for every norm
    norms_dict = {}
    legend_plot_list=[]
    legend_label_list=[]

    for case, norms in cases_results:
        for key, value in norms.items():
            norms_dict.setdefault(key, [])
            norms_dict[key].append( (case, value) )

    plt.hold(True)
    # format tables, ih as inner index
    # compute estimate of order convergence according to d_frac
    for key, norm in norms_dict.iteritems():
        norms_dict[key], plot = single_table(key, norm)
        print plot
        if plot:
            legend_plot_list+=plot[0]
            legend_label_list+=plot[1]
       

    plt.title(r'$L^2(\Omega_f)$ and $L^\infty(\Omega_f)$ norm of the error of approximation of $\partial_x^2 u_f$.')
    plt.xlabel(r'fracture width $\delta$')
    plt.xlim(5e-4, 0.5)
    plt.ylabel('error')    
    plt.legend(legend_plot_list, legend_label_list, 
               loc='upper left',
               title=r'norm, $h$')
    plt.grid(True)
    pp = PdfPages("plot.pdf")
    plt.savefig(pp, format='pdf')
    pp.close()

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
                    norms_list.append( json.load(f) )
    with open(all_norms, "w") as f:
        json.dump(norms_list, f)



  
def main():
    all_norms_file='norms_all.json'
    #if not os.path.isfile(all_norms_file):
    #    colect_norms(all_norms_file)

    with open(all_norms_file, "r") as f:
        norms_list = json.load(f)

    tables_dict=make_table( norms_list )
    #for key, table in tables_dict.iteritems():
    #    make_graph(key, table)
    
    
    write_tables(tables_dict, "norms_table.csv")

        
        
if __name__ == "__main__":
   main()
