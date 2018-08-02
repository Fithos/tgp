package ch.usi.dag.tgp.util;

/**
 * <h1>Properties</h1>
 * This class contains helper methods for managing system properties.
 */ 
public class Properties {
	
	private Properties() {
		// Prevents instantiation. 
	}
		
	public static String stringFromProperty(String propertyName) {
		return stringFromPropertyOrDefault(propertyName, null);
	}

	public static String stringFromPropertyOrDefault(String propertyName, String defaultString) {
		String property = System.getProperty(propertyName);
		return property != null ? property : defaultString;
	}
}