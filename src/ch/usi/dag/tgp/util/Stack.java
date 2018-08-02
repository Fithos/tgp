package ch.usi.dag.tgp.util;

/**
 * <h1>Stack</h1>
 * This class provides a stack, with a similar implementation to java.util.Stack.
 * The purpose of this class is to allow the use of a stack-like data structure, without actually resorting to a class offered by the Java class library, 
 * which would cause DiSL to insert a bypass, increasing the profiling overhead of tgp. 
 */ 
public class Stack<T> {

	private static final int FACTOR = 2;
	private static final int DEFAULT_INITIAL_SIZE = 1024;
	private static final String SEPARATOR = "!";

	private Object[] stack;
	private int tos;

	public Stack(final int size) {
		stack = new Object[size];
		tos = 0;
	}

	public Stack() {
		this(DEFAULT_INITIAL_SIZE);
	}

	public void push(final T elem) {

		if (tos >= stack.length) {			
			resize();
		}
		stack[tos++] = elem;
	}

	@SuppressWarnings("unchecked")
	public T pop() {
		if (tos > 0) {
			final T res = (T) stack[--tos];
			stack[tos] = null;
			return res;
		} else {
			return null;
		}
	}

	@SuppressWarnings("unchecked")
	public T peek() {
		if (tos > 0) {
			final T res = (T) stack[tos-1];
			return res;
		} else {
			return null;
		}
	}

	public void addTop(final long elem) {
		if (tos > 0) {
			final long current = (long) stack[tos-1];
			stack[tos-1]= current + elem;
		}
		else
			stack[0]= elem;
	}

	public void subTop(final long elem) {
		if (tos > 0) {
			final long current = (long) stack[tos-1];
			stack[tos-1]= current - elem;
		}
		else
			stack[0]= elem;
	}

	public boolean contains(final T elem) {
		for (int i = tos - 1; i >= 0; --i) {
			if (stack[i] == elem) {
				return true;
			}
		}
		return false;
	}

	private void resize() {
		final Object[] newArray = new Object[stack.length * FACTOR];
		for (int i = 0; i < stack.length; ++i) {
			newArray[i] = stack[i];
		}
		stack = newArray;
	}

	@Override
	public String toString(){
		StringBuilder sb = new StringBuilder();

		for (int i = 0; i < stack.length; ++i) {
			if(stack[i]!=null)
				sb.append(stack[i]).append(SEPARATOR);
		}		
		return sb.toString();
	}
}