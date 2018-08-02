package ch.usi.dag.tgp.util;

/**
 * <h1>Utils</h1>
 * This class contains a collection of utility methods.
 */ 
public class Utils {

	public static boolean contains(Object[] arr, Object target) {
		for (Object obj: arr) {
			if (obj.equals(target)) {
				return true;
			}						
		}

		return false;
	}

	public static int max(int num1, int num2) {
		return num1 >= num2 ? num1 : num2;
	}

	public static int min(int num1, int num2) {
		return num1 <= num2 ? num1 : num2;
	}
}