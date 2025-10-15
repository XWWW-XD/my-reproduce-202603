import inspect

def ground_truth_process_graph(graph_data):
    clusters = nx.community.louvain_communities(graph_data)
    cluster_dict = dict()
    for clusterindex in range(len(clusters)):
        for n in clusters[clusterindex]:
            cluster_dict[n] = clusterindex
    nx.set_node_attributes(g2['data'], cluster_dict, 'Louvain Communities ClusterID')
    return {'type': 'graph', 'data': graph_data}

import pdb; pdb.set_trace()
print(inspect.getsource(ground_truth_process_graph))
