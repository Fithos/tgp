package ch.usi.dag.tgp.test;

import org.junit.Test;

public class TestProducerConsumer {

	public static class BoundedBuffer<T> {

		private T[] elements;
		private int size;
		private int next;

		public BoundedBuffer(int size) {
			this.size = size;
			this.next = 0;
			this.elements = (T[]) new Object[size];		
		}

		public synchronized boolean isEmpty() {
			return next == 0;
		}

		public synchronized boolean isFull() {
			return next == size;
		}
		
		public synchronized void insert(T element) {
			while (isFull()) {
				__wait();
			}
			__insert(element);
			System.out.println("Notify");
			notify();		
		}

		public synchronized void remove() {
			while (isEmpty()) {
				__wait();
			}
			__remove();
			System.out.println("Notify");
			notifyAll();		
		}

		private void __wait() {
			try {
				System.out.println("Wait");
				wait(1, 1); 	
			} catch (Exception e) {}
		}

		private void __insert(T element) {				
			elements[next++] = element;
		}

		private void __remove() {
			elements[--next] = null;
		}
	}

	public static class ProducerThread extends Thread {

		private BoundedBuffer<Integer> buffer;

		public ProducerThread(BoundedBuffer<Integer> buffer) {
			this.buffer = buffer;			
		}

		public void run() {
			for (int i = 0; i < 1000; i++) {
				buffer.insert(i);
			}			
		}
	}

	public static class ConsumerThread extends Thread {

		private BoundedBuffer<Integer> buffer;

		public ConsumerThread(BoundedBuffer<Integer> buffer) {
			this.buffer = buffer;			
		}

		public void run() {
			for (int i = 0; i < 1000; i++) {
				buffer.remove();
			}			
		}
	}

	public static void main(String[] args) {

		BoundedBuffer<Integer> buffer = new BoundedBuffer<>(100);

		for (int i = 0; i < 10; i ++) {
			new ProducerThread(buffer).start();
			new ConsumerThread(buffer).start();
		}
	}
}