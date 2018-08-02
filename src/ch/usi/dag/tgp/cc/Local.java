package ch.usi.dag.tgp.cc;

import ch.usi.dag.dislre.REDispatch;
import ch.usi.dag.tgp.util.ProfileToggle;

/**
 * <h1>Local (Calling-context profiling)</h1>
 * This class contains methods for sending the collected metrics to the ShadowVM when profiling calling contexts.
 */
public class Local {

	private static final String METHOD_PREFIX = "ch.usi.dag.tgp.cc.Remote.";

	private static final short taskCreationID = REDispatch.registerMethod(METHOD_PREFIX + "registerCCTaskInit");
	private static final short taskExecutionID = REDispatch.registerMethod(METHOD_PREFIX + "registerCCTaskExec");
	private static final short taskSubmissionID = REDispatch.registerMethod(METHOD_PREFIX + "registerCCTaskSubmit");

	private Local() {
		//Prevents instantiation
	}

	public static void registerInitCallingContext(final Object task, final String cc) {
		if (ProfileToggle.isProfilingEnabled() && task != null) {

			REDispatch.analysisStart(taskCreationID);

			REDispatch.sendObject(task);			
			REDispatch.sendObjectPlusData(cc);

			REDispatch.analysisEnd();
		}
	}

	public static void registerExecCallingContext(final Object task, final String cc) {
		if (ProfileToggle.isProfilingEnabled() && task != null) {
			REDispatch.analysisStart(taskExecutionID);

			REDispatch.sendObject(task);
			REDispatch.sendObjectPlusData(cc);

			REDispatch.analysisEnd();
		}
	}

	public static void registerSubmitCallingContext(final Object task, final String cc) {
		if (ProfileToggle.isProfilingEnabled() && task != null) {
			REDispatch.analysisStart(taskSubmissionID);

			REDispatch.sendObject(task);
			REDispatch.sendObjectPlusData(cc);

			REDispatch.analysisEnd();
		}
	}
}