package ch.usi.dag.tgp;

/**
 * <h1>TaskProfile</h1>
 * This class contains basic fields required by any task profiles, and is supposed to be extended 
 * by more specific task profiles adding additional fields.
 */
public class TaskProfile {

	public int id = -1;
	public String klass = null;
	public int execNumber = 0;

	public static String[] getHeader() {
		String[] strArray = {
				"ID",
				"Class",
				"Execution N."
		};
		return strArray;
	}

	public String[] toStringArray() {

		String[] strArray = {
				Integer.toString(id),
				klass, 
				Integer.toString(execNumber) 
		};

		return strArray;
	}
}