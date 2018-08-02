package ch.usi.dag.tgp;

import ch.usi.dag.dislreserver.shadow.ShadowObject;
import java.util.concurrent.ConcurrentHashMap;

/**
 * <h1>AbstractTaskProfileHelper</h1>
 * This class contains helper methods for managing task profiling.  
 * Subclasses are expected to implement the method createEmptyTaskProfile(), which provides a new instance of a task profiling.
 */
public abstract class AbstractTaskProfileHelper {

	private volatile ConcurrentHashMap<ShadowObject, Integer> __nOfTaskProfiles;
	private volatile ConcurrentHashMap<TaskAndOrdinal, TaskProfile> __taskProfiles;	

	public AbstractTaskProfileHelper (){
		__nOfTaskProfiles = new ConcurrentHashMap<>();
		__taskProfiles = new ConcurrentHashMap<>();
	}

	private static class TaskAndOrdinal {

		private ShadowObject task;
		private int ordinal;

		public TaskAndOrdinal(ShadowObject task, int ordinal) {
			this.task = task;
			this.ordinal = ordinal;
		}

		@Override 
		public int hashCode() {
			int result = 17;
			result = 31 * result + ordinal;                          
			result = 31 * result + task.hashCode();                  
			return result;
		}

		@Override
		public boolean equals(Object obj) {
			if (obj instanceof TaskAndOrdinal) {
				TaskAndOrdinal tao = (TaskAndOrdinal) obj;

				if (tao.task.equals(task) && tao.ordinal == ordinal) {
					return true;
				}				
			}

			return false;							
		}				
	}

	public synchronized TaskProfile getLastProfileOfTask(ShadowObject task) {
		Integer nExecutions = __nOfTaskProfiles.get(task);

		if (nExecutions == null) {
			return null;
		} 

		return getProfileOfTask(task, nExecutions);
	}

	public TaskProfile getProfileOfTask(ShadowObject task, int ordinal) {
		if (task == null || ordinal <= 0) {
			return null;
		}
		return __taskProfiles.get(new TaskAndOrdinal(task, ordinal));
	}


	public TaskProfile createPrefilledTaskProfile(ShadowObject task) {
		if (task == null) { 
			return null;
		}

		synchronized(this) {

			Integer nExecutions = getNumberOfProfiles(task);

			if (nExecutions == null) {			
				nExecutions = new Integer(1);						
			} else {
				nExecutions = new Integer(nExecutions.intValue() + 1);			
			}

			__setNumberOfProfiles(task, nExecutions);

			TaskProfile profile = createEmptyTaskProfile();

			profile.klass = task.getShadowClass().getName();
			profile.execNumber = nExecutions.intValue();

			__taskProfiles.put(new TaskAndOrdinal(task, nExecutions.intValue()), profile);
			
			return profile;

		}

		
	}

	protected abstract TaskProfile createEmptyTaskProfile();

	public synchronized TaskProfile newOrLastTaskProfile(ShadowObject task) {
		TaskProfile profile = getLastProfileOfTask(task);

		if (profile == null) {
			profile = createPrefilledTaskProfile(task);
		}

		return profile;
	}

	public Object[] getAllTaskProfiles() {		
		return __taskProfiles.values().toArray();	
	}

	public synchronized Integer getNumberOfProfiles(ShadowObject task) {
		return __nOfTaskProfiles.get(task);
	}

	private void __setNumberOfProfiles(ShadowObject task, Integer nExecutions) {
		__nOfTaskProfiles.put(task, nExecutions);
	}
}
