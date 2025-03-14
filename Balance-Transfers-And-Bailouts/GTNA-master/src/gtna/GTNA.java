/* ===========================================================
 * GTNA : Graph-Theoretic Network Analyzer
 * ===========================================================
 *
 * (C) Copyright 2009-2011, by Benjamin Schiller (P2P, TU Darmstadt)
 * and Contributors
 *
 * Project Info:  http://www.p2p.tu-darmstadt.de/research/gtna/
 *
 * GTNA is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * GTNA is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 *
 * ---------------------------------------
 * GTNA.java
 * ---------------------------------------
 * (C) Copyright 2009-2011, by Benjamin Schiller (P2P, TU Darmstadt)
 * and Contributors
 *
 * Original Author: benni;
 * Contributors:    -;
 *
 * Changes since 2011-05-17
 * ---------------------------------------
 *
 */
package gtna;

import gtna.data.Series;
import gtna.graph.Graph;
import gtna.io.graphWriter.GtnaGraphWriter;
import gtna.metrics.Metric;
import gtna.metrics.basic.DegreeDistribution;
import gtna.metrics.basic.ShortestPaths;
import gtna.networks.Network;

import gtna.plot.Plotting;
import gtna.transformation.Transformation;
import gtna.transformation.edges.Bidirectional;
import gtna.transformation.id.RandomRingIDSpace;
import gtna.util.Config;
import gtna.util.Util;
import gtna.networks.p2p.chord.*;
import gtna.networks.p2p.chord.Chord.IDSelection;
import java.util.concurrent.TimeUnit;
import java.time.Duration;
import java.time.Instant;

/**
 * @author benni
 *
 */
public class GTNA {

public static void main(String[] args) {
 Config.overwrite("SKIP_EXISTING_DATA_FOLDER", "false");
 // GTNA.example1();
  GTNA.example2();
 // GTNA.example3();
 // GTNA.example4();
 // GTNA.example5();
 // GTNA.example6();
 //GTNA.example7();
}

/**
 * @return
 */
//private static gtna.networks.p2p.chord.Chord.IDSelection IDSelection() {
 // TODO Auto-generated method stub
 
 //return RANDOM;
//}




private static void example2() {
 
 
	Instant start1 = Instant.now();
 Config.overwrite("MAIN_DATA_FOLDER", "./data/example2/");
 Config.overwrite("MAIN_PLOT_FOLDER", "./plots/example2/");
 // Config.overwrite("METRICS", "DEGREE_DISTRIBUTION");
 Metric[] metrics = new Metric[] { new DegreeDistribution() };

 //Network nw1 = new ErdosRenyi(100, 5, false, null);
 //Series s1 = Series.generate(nw1, metrics, 5);
 //Plotting.multi(s1, metrics, "er-unidirectional/");

// Network nw2 = new ErdosRenyi(100, 5, true, null);
 //Series s2 = Series.generate(nw2, metrics, 10);
 //Plotting.multi(s2, metrics, "er-bidirectional/");

 //Series[] s = new Series[] { s1, s2 };
 //Plotting.multi(s, metrics, "er-both/");
 
 //IDSelection selection;
 
 Transformation t1 = new Bidirectional();
 Transformation[] t = new Transformation[] { t1 };
 
 Network nw3 =  new Chord(10000, 100, 20, IDSelection.RANDOM, t);
 Series s3 = Series.generate(nw3, metrics, 10);
 Instant finish1 = Instant.now();
long timeElapsed1 = Duration.between(start1, finish1).toMillis();
System.out.println("Time Elapsed for setup is:"+timeElapsed1);
}

private static void example3() {
 Config.overwrite("MAIN_DATA_FOLDER", "./data/example2/");
 Config.overwrite("MAIN_PLOT_FOLDER", "./plots/example3/");
 // Config.overwrite("METRICS", "DEGREE_DISTRIBUTION");
 Metric[] metrics = new Metric[] { new DegreeDistribution() };

 Network nw1 = new ErdosRenyi(100, 5, false, null);
 Network nw2 = new ErdosRenyi(100, 5, true, null);
 Network[] nw = new Network[] { nw1, nw2 };
 Series[] s = Series.get(nw, metrics);
 Plotting.multi(s, metrics, "er-get/");
}

private static void example4() {
 Config.overwrite("MAIN_DATA_FOLDER", "./data/example4/");
 Config.overwrite("MAIN_PLOT_FOLDER", "./plots/example4/");
 // Config.overwrite("METRICS", "DEGREE_DISTRIBUTION");
 Metric[] metrics = new Metric[] { new DegreeDistribution() };

 Transformation t1 = new Bidirectional();
 Transformation[] t = new Transformation[] { t1 };
 Network nw1 = new ErdosRenyi(100, 5, false, null);
 Network nw2 = new ErdosRenyi(100, 5, false, t);
 Network[] nw = new Network[] { nw1, nw2 };
 Series[] s = Series.generate(nw, metrics, 10);
 Plotting.multi(s, metrics, "er-transformed/");
}

private static void example5() {
 Config.overwrite("MAIN_DATA_FOLDER", "./data/example5/");
 Config.overwrite("MAIN_PLOT_FOLDER", "./plots/example5/");
 // Config.overwrite("METRICS", "DEGREE_DISTRIBUTION");
 Metric[] metrics = new Metric[] { new DegreeDistribution() };

 Network[] nw = ErdosRenyi.get(100, new double[] { 5, 6, 7, 8, 9, 10 },
   false, null);
 Series[] s = Series.generate(nw, metrics, 7);
 Plotting.single(s, metrics, "er-singles/");
}

private static void example6() {
 Config.overwrite("MAIN_DATA_FOLDER", "./data/example6/");
 Config.overwrite("MAIN_PLOT_FOLDER", "./plots/example6/");
 // Config.overwrite("METRICS", "CLUSTERING_COEFFICIENT, "
 // + "DEGREE_DISTRIBUTION, " + "RICH_CLUB_CONNECTIVITY, "
 // + "ROUTING, " + "SHORTEST_PATHS, " + "STRONG_CONNECTIVITY, "
 // + "WEAK_CONNECTIVITY");
 Metric[] metrics = new Metric[] { new DegreeDistribution() };

 Transformation t1 = new RandomRingIDSpace(true);
 Transformation t2 = new Bidirectional();
 Transformation[] t = new Transformation[] { t1, t2 };

 // RoutingAlgorithm ra = new Greedy();

 Network[] nw1 = ErdosRenyi.get(100, new double[] { 5, 6, 7, 8, 9, 10 },
   false, t);
 Network[] nw2 = ErdosRenyi.get(200, new double[] { 5, 6, 7, 8, 9, 10 },
   false, t);
 Network[] nw3 = ErdosRenyi.get(300, new double[] { 5, 6, 7, 8, 9, 10 },
   false, t);
 Network[][] nw = new Network[][] { nw1, nw2, nw3 };
 Series[][] s = Series.generate(nw, metrics, 3);
 Series[] s1 = Series.get(nw1, metrics);
 Series[] s2 = Series.get(nw2, metrics);
 Series[] s3 = Series.get(nw3, metrics);
 Plotting.multi(s, metrics, "er-more-singles/");
 Plotting.multi(s1, metrics, "er-more-multi-1/");
 Plotting.multi(s2, metrics, "er-more-multi-2/");
 Plotting.multi(s3, metrics, "er-more-multi-3/");
 Plotting.multi(Util.combine(s), metrics, "er-more-multi/");
}

private static void example7() {
 Config.overwrite("MAIN_DATA_FOLDER", "./data/example7/");
 Config.overwrite("MAIN_PLOT_FOLDER", "./plots/example7/");
 // Config.overwrite("METRICS", "SHORTEST_PATHS");
 Metric[] metrics = new Metric[] { new ShortestPaths() };

 Config.overwrite("SKIP_EXISTING_DATA_FOLDERS", "true");
 Network nw1 = new ErdosRenyi(100, 5, false, null);
 Series s1 = Series.generate(nw1, metrics, 5);
 Series s2 = Series.generate(nw1, metrics, 10);
}
}
