package ch.usi.dag.tgp.task;

import ch.usi.dag.tgp.TaskProfile;

/**
 * <h1>GranularityTaskProfile</h1>
 * This class stores metrics collected during task-granularity profiling.   
 */
public class GranularityTaskProfile extends TaskProfile {

	public int outerTask = -1;
	public int creationThreadID = -1;
	public String creationThreadName = null;
	public String creationThreadClass = null;
	public int executionThreadID = -1;
	public String executionThreadName = null;
	public String executionThreadClass = null;
	public int executorID = -1;
	public String executorClass = null;
	public long entryExecutionTime = -1;
	public long granularity = 0;
	public long exitExecutionTime = -1;
	public boolean isThread = false;
	public boolean isRunnable = false; 
	public boolean isCallable = false;
	public boolean isForkJoinTask = false;
	public boolean isRunExecuted = false;
	public boolean isCallExecuted = false;
	public boolean isExecExecuted = false;

	public String[] toStringArray() {

		String[] strArray = {
				Integer.toString(id),
				klass, 
				Integer.toString(outerTask), 
				Integer.toString(execNumber),
				Integer.toString(creationThreadID),
				creationThreadClass, 
				creationThreadName,
				Integer.toString(executionThreadID),
				executionThreadClass, 
				executionThreadName, 
				Integer.toString(executorID),
				executorClass, 
				Long.toString(entryExecutionTime),
				Long.toString(exitExecutionTime),
				Long.toString(granularity),
				__tof(isThread),
				__tof(isRunnable),
				__tof(isCallable),
				__tof(isForkJoinTask),
				__tof(isRunExecuted),
				__tof(isCallExecuted),
				__tof(isExecExecuted),

		};

		return strArray;
	}

	public static String[] getHeader() {

		String[] header =   {	
				"ID",
				"Class",
				"Outer Task ID", 
				"Execution N.",
				"Creation thread ID",
				"Creation thread class", 
				"Creation thread name", 
				"Execution thread ID",
				"Execution thread class", 
				"Execution thread name", 
				"Executor ID", 
				"Executor class", 
				"Entry execution time", 
				"Exit execution time", 
				"Granularity",
				"Is Thread",
				"Is Runnable",
				"Is Callable",
				"Is ForkJoinTask",
				"Is run() executed",
				"Is call() executed",
				"Is exec() executed",
		};

		return header;
	}

	private static String __tof(boolean b) {
		return b ? "T" : "F";
	}
}