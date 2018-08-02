package ch.usi.dag.tgp.test;

public class TestMultipleTaskExecutions {

	static MyRunnable runnable = new MyRunnable();
	
	private static class MyRunnable implements Runnable {

		@Override
		public void run() {
			System.out.println("I am just a runnable.");			
		}
		
		
		
	}
	
	public static void main(String[] args) {

		
		for (int i = 0; i < 100; i++) {
			runnable.run();
		}
		
		System.out.println("Finish");

	}

}
