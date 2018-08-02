package ch.usi.dag.tgp.test;

import org.junit.Test;

public class TestRunAndJoin {
	
	static int j = 0;
	
	static class ThreadRunner extends Thread {
		
		public void run() {
			
			for (int i = 0; i < 100; i++) {
				j++;
			}
		}
	}
	
	@Test
	public static void main(String[] args) {
		
		Thread[] arr = new Thread[1000];
		
		for (int i = 0; i < 1000; i++) {
			arr[i] = new ThreadRunner();
			arr[i].start();
		}
		
		System.gc();
		
		for (int i = 0; i < 1000; i++) {		
			try { 
				arr[i].join(10, 1);
			} catch (Exception e ) {}
		}
		
		System.out.println("Finish");
	}
}