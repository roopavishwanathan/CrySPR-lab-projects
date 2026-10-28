graph ={22: [645, 22], 74: [645, 22], 94: [645, 22], 645: [645, 22], 909: [645, 22]}

# function to generate all possible paths
def find_all_paths(graph, start, end, path=[]):
    path = path + [start]
    if start == end:
        return [path]
    paths = []
    for node in graph[start]:
        if node not in path:
            newpaths = find_all_paths(graph, node, end, path)
        for newpath in newpaths:
            paths.append(newpath)
    return paths


# Driver function call to print all
# generated paths
print(find_all_paths(graph, 22, 94))