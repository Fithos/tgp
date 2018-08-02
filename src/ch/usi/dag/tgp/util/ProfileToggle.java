package ch.usi.dag.tgp.util;

public class ProfileToggle {

	private static final String PROFILE_PROPERTY_NAME = "tgp.profile";
	
	/* Default value is true. 
	 * If the profiler shall start profiling at a later time (e.g., due to 
	 * warmup iterations) set the system property tgp.profile to false, 
	 * and call enableProfiling().  
	 * 
	 */
	private static boolean profileEnabled;

	static {
		String property = Properties.stringFromProperty(PROFILE_PROPERTY_NAME);
		profileEnabled =  (property != null && property.equals("false")) ? false : true;					
	}
	
	public static void enableProfiling(){
		profileEnabled = true;
	}
	
	public static void disableProfiling(){
		profileEnabled = false;
	}

	public static boolean isProfilingEnabled(){	
		return profileEnabled;
	}
}