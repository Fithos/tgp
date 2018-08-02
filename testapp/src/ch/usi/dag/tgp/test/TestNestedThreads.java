package ch.usi.dag.tgp.test;

public class TestNestedThreads implements Runnable {
    
	public TestNestedThreads(){}

	@Override
	public void run(){
		double[][]dp = new double [4][4];
		for (int i = 0; i < dp.length; i++) {
			for (int j = 0; j < dp[i].length; j++) {
				dp[i][j] = i*j;
			}
		}

		Thread t2 = new Thread(new OtherClass1());
		t2.start();

		Thread t3 = new Thread(new OtherClass2());
		t3.start();
	}

	public static void main(String[] args) {
		System.out.println("********* TestNestedThreads.java: Testing outer task profiling *********");
		Thread t1 = new Thread(new TestNestedThreads());
		t1.start();
	}

}

class OtherClass1 implements Runnable {

	public OtherClass1(){}

	@Override
	public void run() {
		int x = 0; 
	}
	
}

class OtherClass2 implements Runnable {

	public OtherClass2(){}

	@Override
	public void run() {
		int y = 0; 
	}
	
}
