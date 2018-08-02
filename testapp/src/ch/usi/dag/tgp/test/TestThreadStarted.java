package ch.usi.dag.tgp.test;

class DirectThreadWithoutRun extends Thread {		
	}
	
	class DirectThreadWithRun extends Thread {
		public void run() {
			System.out.println("I am a DirectThreadWithRun");
		}
	}
	
	class DirectRunnable implements Runnable {

		@Override
		public void run() {
			System.out.println("I am a DirectRunnable");
		}
	}
	
	class SubtypeOfDirectRunnable extends DirectRunnable {}
	
	abstract class AbstractClass {
		abstract void test();
	}

public class TestThreadStarted {

	public static void main(String[] argv) {
		
		Runnable startedThreadWithoutRun = new DirectThreadWithoutRun();
		((Thread) startedThreadWithoutRun).start();
				
		Runnable notStartedThreadWithRun = new DirectThreadWithRun();
		System.out.println(notStartedThreadWithRun.toString());
				
		Runnable startedThreadWithRun = new DirectThreadWithRun();
		((Thread) startedThreadWithRun).start();
		
		new Thread(new DirectRunnable()).start();
		
		new Thread(new Runnable() {
			@Override
			public void run() {				
				System.out.println("I am a Runnable created on the fly!");
			}
		}).start();
		
		Runnable newRunnable = new SubtypeOfDirectRunnable();
		new Thread (newRunnable).start();
				
		new Thread (new SubtypeOfDirectRunnable()).start();
	}
}