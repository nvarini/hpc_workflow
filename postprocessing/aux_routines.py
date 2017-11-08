import numpy as np

def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() , 1.00*height, '%.1f' % height,
        ha='center', va='bottom',rotation=45)

def all_same(items):
    return all(x == items[0] for x in items)

def create_plot_array(defdict):
    count=0
    tempi_per_plot=[]
    for k,v in defdict.iteritems():
        tempi_per_plot.append(v[0])    
        count+=1
    return  np.array([sum(x)/float(count) for x in zip(*tempi_per_plot)])

