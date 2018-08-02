package ch.usi.dag.tgp.cc;

import ch.usi.dag.dislreserver.remoteanalysis.RemoteAnalysis;
import ch.usi.dag.dislreserver.shadow.ShadowObject;
import ch.usi.dag.tgp.TaskProfile;
import ch.usi.dag.tgp.AbstractTaskProfileHelper;
import ch.usi.dag.tgp.util.CSVDumper;
import ch.usi.dag.tgp.util.Properties;

/**
 * <h1>Remote (Calling-context profiling)</h1>
 * This class contains code executed in the ShadowVM to store the metrics received during calling-context profiling.
 */ 
public class Remote extends RemoteAnalysis {

	public class CCTaskProfileHelper extends AbstractTaskProfileHelper {

		@Override
		protected TaskProfile createEmptyTaskProfile() {		
			return new CCTaskProfile();
		}

		public CCTaskProfile createClonedTaskProfile(ShadowObject task, CCTaskProfile sourceTaskProfile) {
			final CCTaskProfile profile = (CCTaskProfile) createPrefilledTaskProfile(task);
			profile.ccInit = sourceTaskProfile.ccInit;
			return profile;
		}

	}

	private volatile CCTaskProfileHelper __profileHelper;

	private volatile CSVDumper __taskCSVDumper;

	private static final String TASK_FILE_PROPERTY_NAME = "tgp.csvdumper.task";
	private static final String TASK_FILE_DEFAULT= "profiles/tasks.csv";


	public Remote() {

		__profileHelper = new CCTaskProfileHelper();
		__taskCSVDumper = new CSVDumper(Properties.stringFromPropertyOrDefault(TASK_FILE_PROPERTY_NAME, TASK_FILE_DEFAULT), CCTaskProfile.getHeader());
	}

	public void registerCCTaskInit(final ShadowObject task, final ShadowObject cc  ) {

		/* This method should be called only once per task.
		 * If the method is called a second time, the method does not create a second task profile for the same task.
		 * Instead, it updates the init CC in the already created profile.  
		 */

		final CCTaskProfile prof = (CCTaskProfile) __profileHelper.newOrLastTaskProfile(task);


		prof.id = System.identityHashCode(task); 
		prof.ccInit = cc.toString();
	}


	public void registerCCTaskExec(final ShadowObject task, final ShadowObject cc) {

		/* Case A: If the method is called and no task profile had been created for the task, create the profile and store the exec CC.   
		 * Case B: If the method is called, a single task profile has been created for the task, and no exec CC is stored in the profile, 
		 * 			the task has been created, but not yet executed. Store the exec CC in the already created profile.
		 * Case C: If the method is called, and either 1) a single task profile has been created for the task, with the exec CC already stored, or
		 * 			2) multiple task profiles for the task have been created, the task is being executed multiple times. Create a new task profile, copying 
		 * 			the init CC from an already existing profile for the same task. 
		 */

		final Integer nProfiles = __profileHelper.getNumberOfProfiles(task);
		final CCTaskProfile prof; 

		if (nProfiles == null) { //Case A
			prof = (CCTaskProfile) __profileHelper.createPrefilledTaskProfile(task);
		} else if (nProfiles.intValue() == 1 && ((CCTaskProfile) __profileHelper.getProfileOfTask(task, 1)).ccExec == null) { //Case B
			prof = (CCTaskProfile) __profileHelper.getProfileOfTask(task, 1); 
		} else { //Case C
			prof = (CCTaskProfile) __profileHelper.createClonedTaskProfile(task, (CCTaskProfile) __profileHelper.getLastProfileOfTask(task));
		}

		prof.id = System.identityHashCode(task); 
		prof.ccExec = cc.toString();
	}

	public void registerCCTaskSubmit(final ShadowObject task, final ShadowObject cc  ) {

		/* Submission to a task execution framework is registered in the last task profile stored for the task.     
		 * If no task profile has been created for the task, create it.  
		 */

		final CCTaskProfile prof = (CCTaskProfile) __profileHelper.newOrLastTaskProfile(task);

		prof.id = System.identityHashCode(task); 
		prof.ccSubmit = cc.toString();
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