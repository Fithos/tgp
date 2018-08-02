package ch.usi.dag.tgp.cc;

import ch.usi.dag.tgp.TaskProfile;

/**
 * <h1>CCTaskProfile</h1>
 * This class stores metrics collected during calling-context profiling.   
 */
public class CCTaskProfile extends TaskProfile {

	public String ccInit = null;
	public String ccExec = null;
	public String ccSubmit = null;

	public String[] toStringArray() {

		String[] strArray = {
				Integer.toString(id),
				klass, 
				Integer.toString(execNumber), 
				ccInit,
				ccSubmit,
				ccExec				
		};

		return strArray;
	}

	public static String[] getHeader() {

		String[] header =  {	
				"ID",
				"Class",			
				"Execution N.",
				"Calling Context (init)",
				"Calling Context (submit)",
				"Calling Context (exec)"				
		};

		return header;
	}
}