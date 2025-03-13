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

import gtna.util.Config;
import java.util.HashMap;
import gtna.graph.Edges;
import gtna.graph.Edge;

import treeembedding.treerouting.*;
import treeembedding.vouteoverlay.Treeembedding;
import java.util.Random;

import gtna.graph.Node;
import treeembedding.treerouting.Treeroute;

import java.util.concurrent.TimeUnit;
import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.Iterator;
import java.util.Set;
import java.io.File;
import java.io.FileReader;









public class Bailout {
	public static void main(String[] args) throws IOException
	{
		
		Config.overwrite("SKIP_EXISTING_DATA_FOLDER", "false");
		String path = "/Documents/data_testf/";
		
		Graph graph = Bailout.example7();
		Random rand = null;
		Treeroute rs;
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
		System.out.println("the line is :" +text);
		String msg = text;
		BufferedWriter writer2 = new BufferedWriter(new FileWriter("./data/neighbor.txt"));
		writer2.write(text);
		writer2.close();
		
	String filePATH = "./data/neighbor.txt";
	HashMap<String, String> map = new HashMap<String, String>();

    String line;
    BufferedReader reader = new BufferedReader(new FileReader(filePATH));
    while ((line = reader.readLine()) != null)
    {
        String[] parts = line.split(":", 2);
        if (parts.length >= 2)
        {
            String key = parts[0];
            String value = parts[1];
            map.put(key, value);
        } else {
            System.out.println("ignoring line: " + line);
        }
    }

    for (String key : map.keySet())
    {
        System.out.println(key + ":" + map.get(key));
    }
    reader.close();
}
	
		

	

	
	
		
		int [] y = d.getRoute(460, 20, 0, g2, n);
		final long startTime = System.currentTimeMillis();
		Edges edges = g2.getEdges();
		
		edges.add(67, 999);
		final long endTime = System.currentTimeMillis();

		System.out.println("edge establishment time is : " + (endTime - startTime));
			
		edges.fill();
		
		
		
	}
	
	
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
			
			

			new GtnaGraphWriter().writeWithProperties(g, "./data/firstExample-graph.graph");
			new GtnaGraphWriter().writeWithProperties(g, "./data/firstExample-graph.txt");
			
			
			
			
			
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
	
	
	
	
