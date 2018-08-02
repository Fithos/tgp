package ch.usi.dag.tgp.task;

import ch.usi.dag.dislreserver.remoteanalysis.RemoteAnalysis;
import ch.usi.dag.dislreserver.shadow.ShadowObject;
import ch.usi.dag.dislreserver.shadow.ShadowString;
import ch.usi.dag.dislreserver.shadow.ShadowThread;
import ch.usi.dag.tgp.util.CSVDumper;
import ch.usi.dag.tgp.util.Properties;
import ch.usi.dag.tgp.TaskProfile;
import ch.usi.dag.tgp.AbstractTaskProfileHelper;
import ch.usi.dag.tgp.task.GranularityTaskProfile;

/**
 * <h1>Remote (task-granularity profiling)</h1>
 * This class contains code executed in the ShadowVM to store the metrics received during task-granularity profiling.
 */ 
public class Remote extends RemoteAnalysis {

	public class GranularityTaskProfileHelper extends AbstractTaskProfileHelper {

		@Override
		protected TaskProfile createEmptyTaskProfile() {		
			return new GranularityTaskProfile();
		}

		public GranularityTaskProfile createClonedTaskProfile(ShadowObject task, GranularityTaskProfile sourceTaskProfile) {
			final GranularityTaskProfile profile = (GranularityTaskProfile) createPrefilledTaskProfile(task);
			profile.creationThreadClass = sourceTaskProfile.creationThreadClass;
			profile.creationThreadID = sourceTaskProfile.creationThreadID;
			profile.creationThreadName = sourceTaskProfile.creationThreadName;				
			profile.isCallable = sourceTaskProfile.isCallable;
			profile.isForkJoinTask = sourceTaskProfile.isForkJoinTask;
			profile.isRunnable = sourceTaskProfile.isRunnable;
			profile.isThread = sourceTaskProfile.isThread;

			return profile;
		}

		public boolean hasInfoAboutExecution(GranularityTaskProfile profile) {
			if (profile.entryExecutionTime == -1 && profile.exitExecutionTime == -1 && profile.granularity == 0) {
				return true;
			}
			return false;			
		}
	}

	private volatile GranularityTaskProfileHelper __profileHelper;
	private volatile CSVDumper __taskCSVDumper;

	private static final String TASK_FILE_PROPERTY_NAME = "tgp.csvdumper.task";
	private static final String TASK_FILE_DEFAULT= "profiles/tasks.csv";

	public Remote() {
		__profileHelper = new GranularityTaskProfileHelper();	
		__taskCSVDumper = new CSVDumper(Properties.stringFromPropertyOrDefault(TASK_FILE_PROPERTY_NAME, TASK_FILE_DEFAULT), GranularityTaskProfile.getHeader());
	}

	public void registerTaskCreation(final ShadowObject task, final int taskID, final int taskClassID, final ShadowThread thread, final int threadID) {		

		/* This method should be called only once per task.
		 * If the method is called a second time, the method does not create a second task profile for the same task.
		 * Instead, it updates information related to task creation in the already created profile.  
		 */
		final GranularityTaskProfile prof = (GranularityTaskProfile) __profileHelper.newOrLastTaskProfile(task);

		prof.id = taskID; 

		if (thread != null) {			
			prof.creationThreadID = threadID;
			prof.creationThreadClass = thread.getShadowClass().getName();
			prof.creationThreadName = thread.getName();
		}

		prof.isThread = task instanceof ShadowThread;

		switch (taskClassID) {
		case Local.RUNNABLE_ID: prof.isRunnable = true; break;
		case Local.CALLABLE_ID: prof.isCallable = true; break;
		case Local.FORKJOINTASK_ID: prof.isForkJoinTask = true; break;
		}
	}

	public void registerTaskExecution(final ShadowObject task, final int taskID, final ShadowThread thread, final int threadID, final int outerTask, final long granularity, 
			final ShadowString methodName,  final long entryTime, final long exitTime) {	

		/* Case A: If the method is called and no task profile had been created for the task, create the profile and store info related to task execution.  
		 * Case B: If the method is called, a single task profile has been created for the task, and no info about task execution is stored in the profile, 
		 * 			the task has been created, but not yet executed. Store info related to task execution in the already created profile.
		 * Case C: If the method is called, and either 1) a single task profile has been created for the task, with info about task execution already stored, or
		 * 			2) multiple task profiles for the task have been created, the task is being executed multiple times. Create a new task profile, copying 
		 * 			information about task creation from an already existing profile for the same task. 
		 */


		final GranularityTaskProfile prof; 

		final Integer nProfiles = __profileHelper.getNumberOfProfiles(task);

		if (nProfiles == null) { //Case A
			prof = (GranularityTaskProfile) __profileHelper.createPrefilledTaskProfile(task);
		} else if (nProfiles.intValue() == 1 && __profileHelper.hasInfoAboutExecution((GranularityTaskProfile) __profileHelper.getProfileOfTask(task, 1))) { //Case B
			prof = (GranularityTaskProfile) __profileHelper.getProfileOfTask(task, 1); 
		} else { //Case C
			prof = (GranularityTaskProfile) __profileHelper.createClonedTaskProfile(task, (GranularityTaskProfile) __profileHelper.getLastProfileOfTask(task));
		}


		prof.id = taskID; 

		if (thread != null) {			
			prof.executionThreadID = threadID;
			prof.executionThreadClass = thread.getShadowClass().getName();
			prof.executionThreadName = thread.getName();
		}

		prof.outerTask = outerTask;

		prof.granularity = granularity;
		prof.isThread = task instanceof ShadowThread;		

		switch (methodName.toString()) {
		case "run": prof.isRunExecuted = true; break;
		case "call": prof.isCallExecuted = true; break;
		case "exec": prof.isExecExecuted = true; break;
		}

		prof.entryExecutionTime = entryTime;
		prof.exitExecutionTime = exitTime;
	}

	public void registerTaskSubmission(final ShadowObject task, final int taskID, final ShadowObject executor, final int executorID) {

		/* Submission to a task execution framework is registered in the last task profile stored for the task.     
		 * If no task profile has been created for the task, create it.  
		 */

		final GranularityTaskProfile prof = (GranularityTaskProfile) __profileHelper.newOrLastTaskProfile(task);

		prof.id = taskID;  		
		prof.isThread = task instanceof ShadowThread;		

		prof.executorID = executorID;
		prof.executorClass = executor.getShadowClass().getName(); 

	}

	@Override
	public void atExit() {
		for (Object prof : __profileHelper.getAllTaskProfiles()) {
			__taskCSVDumper.dumpLine(((TaskProfile) prof).toStringArray());
		}
		__taskCSVDumper.closeFile();
	}

	@Override
	public void objectFree(final ShadowObject shadowObject) {
		// Do nothing
	}
}