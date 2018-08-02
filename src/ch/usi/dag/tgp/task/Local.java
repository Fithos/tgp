package ch.usi.dag.tgp.task;

import ch.usi.dag.dislre.REDispatch;
import ch.usi.dag.tgp.util.ProfileToggle;
import ch.usi.dag.tgp.util.Properties;
import cz.cuni.mff.d3s.perf.MultiContextBenchmark;

/**
 * <h1>Local (task-granularity profiling)</h1>
 * This class contains methods for sending the collected metrics to the ShadowVM when profiling task granularity.
 */
public class Local {

	private static final String METHOD_PREFIX = "ch.usi.dag.tgp.task.Remote.";

	private static final short taskCreationID = REDispatch.registerMethod(METHOD_PREFIX + "registerTaskCreation");
	private static final short taskExecutionID = REDispatch.registerMethod(METHOD_PREFIX + "registerTaskExecution");
	private static final short taskSubmissionID = REDispatch.registerMethod(METHOD_PREFIX + "registerTaskSubmission");

	public static final int RUNNABLE_ID = 1;
	public static final int CALLABLE_ID = 2;
	public static final int FORKJOINTASK_ID = 3;	

	private static final String PAPI_METRIC_PROPERTY_NAME = "tgp.papi.event";
	private static final String PAPI_METRIC_DEFAULT= "PAPI_REF_CYC";

	public static final String[] EVENTS = {
			Properties.stringFromPropertyOrDefault(PAPI_METRIC_PROPERTY_NAME, PAPI_METRIC_DEFAULT)
	};

	private Local() {
		//Prevents instantiation
	}

	public static long createPAPIcontext(){
		long context = MultiContextBenchmark.init(1, EVENTS );
		MultiContextBenchmark.start(context);
		return context;
	}

	public static void registerCreation(final Object task, final Thread thread, final int taskClassID) {
		if (ProfileToggle.isProfilingEnabled() && task != null) {

			REDispatch.analysisStart(taskCreationID);

			REDispatch.sendObject(task);
			REDispatch.sendInt(System.identityHashCode(task));
			REDispatch.sendInt(taskClassID);
			REDispatch.sendCurrentThread();
			REDispatch.sendInt(System.identityHashCode(thread));

			REDispatch.analysisEnd();
		}
	}
		
	public static void registerExecution(final Object task, final int taskID, final int outerTask, final long granularity, final long entryTime, final long endTime,
			final Thread thread, final String methodName) {
		if (ProfileToggle.isProfilingEnabled() && task != null) {

			REDispatch.analysisStart(taskExecutionID);

			REDispatch.sendObject(task);
			REDispatch.sendInt(taskID);
			REDispatch.sendCurrentThread();		
			REDispatch.sendInt(System.identityHashCode(thread));
			REDispatch.sendInt(outerTask);
			REDispatch.sendLong(granularity);
			REDispatch.sendObjectPlusData(methodName);
			REDispatch.sendLong(entryTime);
			REDispatch.sendLong(endTime);

			REDispatch.analysisEnd();
		}
	}

	public static void registerSubmission(final Object task, final Object executor) {
		if (ProfileToggle.isProfilingEnabled() && task != null) {

			REDispatch.analysisStart(taskSubmissionID);

			REDispatch.sendObject(task);
			REDispatch.sendInt(System.identityHashCode(task));
			REDispatch.sendObject(executor);
			REDispatch.sendInt(System.identityHashCode(executor));

			REDispatch.analysisEnd();
		}
	}
}