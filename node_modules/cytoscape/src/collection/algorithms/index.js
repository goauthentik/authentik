import * as util from '../../util';
import bfsDfs from './bfs-dfs';
import dijkstra from './dijkstra';
import kruskal from './kruskal';
import aStar from './a-star';
import floydWarshall from './floyd-warshall';
import bellmanFord from './bellman-ford';
import kargerStein from './karger-stein';
import pageRank from './page-rank';
import degreeCentrality from './degree-centrality';
import closenessCentrality from './closeness-centrality';
import betweennessCentrality from './betweenness-centrality';
import markovClustering from './markov-clustering';
import kClustering from './k-clustering';
import hierarchicalClustering from './hierarchical-clustering';
import affinityPropagation from './affinity-propagation';
import hierholzer from './hierholzer';
import hopcroftTarjanBiconnected from './hopcroft-tarjan-biconnected';
import tarjanStronglyConnected from './tarjan-strongly-connected';

var elesfn = {};

[
  bfsDfs,
  dijkstra,
  kruskal,
  aStar,
  floydWarshall,
  bellmanFord,
  kargerStein,
  pageRank,
  degreeCentrality,
  closenessCentrality,
  betweennessCentrality,
  markovClustering,
  kClustering,
  hierarchicalClustering,
  affinityPropagation,
  hierholzer,
  hopcroftTarjanBiconnected,
  tarjanStronglyConnected
].forEach(function(props) {
  util.extend(elesfn, props);
});

export default elesfn;
