import numpy as np

data = np.array([1,2,3,4,3,2,4,7,8,4,3,0,0,0,0,9,9,9,11,23,2,3,4,29,23])

counts, bin_edges = np.histogram(data, bins=4)
# returns a tuple containing two arrays:
# counts: An array containing the number of data points in each bin.
# bin_edges: An array containing the edges of each bin.
#(array([10,  6,  0,  1]), array([ 1. ,  6.5, 12. , 17.5, 23. ]))
print(counts, bin_edges)

edge_from = bin_edges[3]
edge_to = bin_edges[4]
print(edge_from)
print(edge_to)
print("test where", data[np.where((edge_from<data) & (data<edge_to))])

ctvrty_bin = [datum for datum in data if edge_from <= datum <= edge_to]

print(np.mean(ctvrty_bin))

#print(histo[0][-2])

bins = 4
mean_of_4th_bin = np.mean(data[np.where(np.histogram(data, bins)[1][3] <= data)[0]])
# print(mean_of_4th_bin)
# print(mean_of_fourth_bucket)




# Print the data from the 3rd bin using a list comprehension

#print([datum for datum in data if bin_edges[2] <= datum < bin_edges[3]])