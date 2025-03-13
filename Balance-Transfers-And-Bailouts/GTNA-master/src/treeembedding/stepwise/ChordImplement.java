


package treeembedding.stepwise;







import java.util.HashMap;
import java.util.Vector;

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
import treeembedding.stepwise.BalancedCA;


/**
 * @author benni
 *
 */
public class ChordImplement 
{

	public static void main(String[] args)  
{

	
	
	
	






 
 

 //Config.overwrite("MAIN_DATA_FOLDER", "./data/example2/");
 //Config.overwrite("MAIN_PLOT_FOLDER", "./plots/example2/");
 // Config.overwrite("METRICS", "DEGREE_DISTRIBUTION");
 Metric[] metrics = new Metric[] { new DegreeDistribution() };

 //Network nw1 = new ErdosRenyi(100, 5, false, null);
 //Series s1 = Series.generate(nw1, metrics, 5);
 //Plotting.multi(s1, metrics, "er-unidirectional/");

 //Network nw2 = new ErdosRenyi(100, 5, true, null);
 //Series s2 = Series.generate(nw2, metrics, 10);
 //Plotting.multi(s2, metrics, "er-bidirectional/");

 //Series[] s = new Series[] { s1, s2 };
 //Plotting.multi(s, metrics, "er-both/");
 
 //IDSelection selection;
 
 Transformation t1 = new Bidirectional();
 Transformation[] t = new Transformation[] { t1 };
 
 Network nw3 =  new Chord(100, 10, 5, IDSelection.RANDOM, t);
 Graph g = nw3.generate();
 new GtnaGraphWriter().write(g, "./data/firstExample-graph.txt");

 Series s3 = Series.generate(nw3, metrics, 10);
 
 
 
 boolean virtual;
	boolean simple_join;
	int c;
	double est;
	double[][] lastId;
	int initIDs;
	int initMes;
	HashMap<Integer, Integer> nest;
	Vector<Integer> newIDs;
	Vector<Integer> messages;
	Vector<Integer> newIDsTot;
	Vector<Integer> messagesTot;
	Vector<Double> newIDs_frac;
	Vector<Double> mess_frac;
	Vector<Double> maxOverhead;
	Vector<Double> boundOver;
	Vector<Double> jain;
	double[][] frac_ids;
	int[] level_virtual;
	
	  j  = new processJoin(g,nw3, 1,90);
	
	
	
 
 
 
 
}
}




	
	 


