package treeembedding.tests;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Vector;
import java.util.Map;

import gtna.data.Series;
import gtna.graph.Graph;
import gtna.graph.weights.EdgeWeights;
import gtna.io.graphWriter.GtnaGraphWriter;
import gtna.metrics.Metric;
import gtna.metrics.basic.DegreeDistribution;
import gtna.metrics.basic.ShortestPaths;
import gtna.networks.Network;
import gtna.networks.model.ErdosRenyi;
import gtna.plot.Plotting;
import gtna.transformation.Transformation;
import gtna.transformation.edges.Bidirectional;
import gtna.transformation.id.RandomRingIDSpace;
import gtna.transformation.spanningtree.BFSRand;
import gtna.transformation.spanningtree.MultipleSpanningTree;
import gtna.util.Config;
import gtna.util.Util;
import java.util.ArrayList;
import java.util.HashMap;
import gtna.graph.Edges;
import gtna.graph.Edge;
import gtna.graph.weights.EdgeWeights;
import gtna.graph.GraphProperty;
import treeembedding.treerouting.*;
import treeembedding.vouteoverlay.Treeembedding;
import java.util.Random;
import gtna.transformation.spanningtree.BFS;
import gtna.graph.Node;
import treeembedding.treerouting.Treeroute;
import gtna.networks.model.Landmark;
import java.io.*;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Scanner;
import java.util.HashMap;
import java.util.Arrays;
import java.text.ParseException;
import java.util.concurrent.TimeUnit;
import java.time.Duration;
import java.time.Instant;
import java.util.concurrent.TimeUnit;






public class Bailout {

	public static void main(String[] args) throws IOException{
		Config.overwrite("SKIP_EXISTING_DATA_FOLDER", "false");
		String path = "/Documents/data_testf/";
		
		
		// GTNA.example1();
		// GTNA.example2();
		// GTNA.example3();
		// GTNA.example4();
		// GTNA.example5();
		// GTNA.example6();
		Graph graph = Bailout.example7();
		Random rand = null;
		Treeroute rs;

	   // HashMap<Edge, Double> weights;
	    //double weight;
		//double defaultWeight;
		//Edge[] edges = graph.generateEdges();
		//EdgeWeights EdgeWeights(edges, weight, defaultWeight);
		
		//String graph = "./data/firstExample-graph1.txt";
		//String resAdd =  "./data/firstExample-graph2.txt";
		//String resGraph = "./data/hashmap";
		//String add = "./data/ripple_links_history.txt";
		//String name = "./data/RIPPLEJan29";
		//toAddList(graph, resAdd+".txt", map);
		//HashMap<String, Integer> map = turnGraphs(resAdd, resGraph+".graph", name);
		//boolean roots = false;
		//Transformation TBFS =  new BFS();
	 	//Graph g3 = TBFS.transform(graph);
		Treeembedding embeed = new Treeembedding("T",5);
		Graph g2 = embeed.transform(graph);
		Node[] n = g2.getNodes();
		Treeroute d = new TreerouteTDRAP();
		
		String source = "hello am 67 and am the source";
		Instant start1 = Instant.now();
		BufferedWriter writer;
		try 
		{
			writer = new BufferedWriter(new FileWriter("./data/source.txt"));
			writer.write(source);
			writer.close();
			} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			}
		
		
		
		String landmark = "hello am 20 and am the landmark node";
		BufferedWriter writer1;
		try 
		{
			writer1 = new BufferedWriter(new FileWriter("./data/destination.txt"));
			writer1.write(landmark);
			writer1.close();
			} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			}
		Instant finish1 = Instant.now();
		long timeElapsed1 = Duration.between(start1, finish1).toNanos();
		System.out.println("Time Elapsed for Broadcast:"+timeElapsed1);
			
		
		
		//System.out.println("hello am 67 and am the source");
		//System.out.println("hello am 20 and am the landmark");
		//int[] x = d.getRoute(20, 67, 0, g2, n);
		String text = "";
		int linenum;
		try {
			FileReader readfile = new FileReader("./data/firstExample-graph.txt");
			 BufferedReader readbuffer = new BufferedReader(readfile);
			for (linenum = 1; linenum <1010;linenum++)
			{
			if (linenum == 28)
				{
					text = readbuffer.readLine();
					
				} else {
					readbuffer.readLine();
				}
			}
			}catch (IOException e)
			{
				e.printStackTrace();
			}
		//System.out.println("the line is :" +text);
		String msg = text;
		BufferedWriter writer2 = new BufferedWriter(new FileWriter("./data/neighbor.txt"));
		writer2.write(text);
		writer2.close();
		
		
		int [] y = d.getRoute(460, 20, 0, g2, n);
		final long startTime = System.currentTimeMillis();
		Edges edges = g2.getEdges();
		
		edges.add(67, 460);
		final long endTime = System.currentTimeMillis();

		System.out.println("edge establishment time is : " + (endTime - startTime));
			
		edges.fill();
		
		//new GtnaGraphWriter().writeWithProperties(g2, "./data/thirdExample-graph2.txt");
		
		
		
		
		
		
		
		
		
		
		 
	
		
		
		
		
		
		
		
		
					
	

		
		
		
		
	
		
		//File file = new File("./data/firstExample-graph2.graph");
		
		//new GtnaGraphWriter().writeWithProperties(g3, "./data/firstExample-graph3.graph");
		
		
	}
	
	//Creating function to generate a graph 
	private static Graph example7() {
		long startTime = System.nanoTime();
		
		Metric[] metrics = new Metric[] { new DegreeDistribution() };
			double weights;
			Metric ra;

			Network nw1 = new ErdosRenyi(1000,25 , true, null);
			
			Graph g = nw1.generate();
			Edge[] e = g.generateEdges();
			new GtnaGraphWriter().writeWithProperties(g, "./data/firstExample-graph.txt");
			
			
			
			
	
			
			EdgeWeights nw2 = new EdgeWeights(e,4, 0);
			g.addProperty(g.getNextKey("ID_SPACE"), nw2);
			//Treeroute nw = computeData(g,nw1,HashMap<String, metrics> m );
			
			//int[] arr = g.getRoute(3,99,0,g,g.getNodes());
			
			

			new GtnaGraphWriter().writeWithProperties(g, "./data/firstExample-graph.graph");
			new GtnaGraphWriter().writeWithProperties(g, "./data/firstExample-graph.txt");
			
			
			//new GraphProperty().write("./data/firstExample-graphprop.txt", nw2)
			//new GtnaGraphWriter().write(nw2, "./data/firstExample-graphedge.txt");
					
		//	Map<Integer, List> graph = new HashMap<>();
			
			
			long  endTime = System.nanoTime();
			long durationInNano = (endTime - startTime);
			long durationInMillis = TimeUnit.NANOSECONDS.toMillis(durationInNano); 
			System.out.println("the setup time is " +durationInMillis);
			return g;
		}
			public static double getRandomNumber(){

					double x = Math.random();

					return x;
			}

	}
	
	
	
	
