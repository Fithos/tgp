package ch.usi.dag.tgp.guard;

import ch.usi.dag.disl.annotation.GuardMethod;
import ch.usi.dag.disl.guardcontext.GuardContext;
import ch.usi.dag.disl.guardcontext.ReflectionStaticContext;
import ch.usi.dag.disl.staticcontext.MethodStaticContext;
import ch.usi.dag.tgp.util.Properties;
import ch.usi.dag.tgp.util.Utils;

/**
 * <h1>GuardsPreprocessing</h1>
 * This class contains guards that use the DiSL Reflection API as well as preprocessed reflective supertype information of the Java class library. 
 */
public class GuardsPreprocessing {

	private static final String TASK_EXEC_PREPROCESS_FILE_PROPERTY_NAME = "tgp.preprocess.task.exec";
	private static final String TASK_EXEC_PREPROCESS_FILE_DEFAULT= "input/task-exec-typegraph.ser";

	private static final String RUNNABLE_INIT_PREPROCESS_FILE_PROPERTY_NAME = "tgp.preprocess.runnable.init";
	private static final String RUNNABLE_INIT_PREPROCESS_FILE_DEFAULT= "input/runnable-init-typegraph.ser";

	private static final String CALLABLE_INIT_PREPROCESS_FILE_PROPERTY_NAME = "tgp.preprocess.callable.init";
	private static final String CALLABLE_INIT_PREPROCESS_FILE_DEFAULT= "input/callable-init-typegraph.ser";

	private static final String FORKJOINTASK_INIT_PREPROCESS_FILE_PROPERTY_NAME = "tgp.preprocess.forkjointask.init";
	private static final String FORKJOINTASK_INIT_PREPROCESS_FILE_DEFAULT= "input/forkjointask-init-typegraph.ser";

	private static final String EXECUTOR_SUBMIT_PREPROCESS_FILE_PROPERTY_NAME = "tgp.preprocess.executor.submit";
	private static final String EXECUTOR_SUBMIT_PREPROCESS_FILE_DEFAULT= "input/executor-submit-typegraph.ser";

	private static PreprocessingHelper taskExecHelper = new PreprocessingHelper(Properties.stringFromPropertyOrDefault(TASK_EXEC_PREPROCESS_FILE_PROPERTY_NAME,TASK_EXEC_PREPROCESS_FILE_DEFAULT));
	private static PreprocessingHelper runnableInitHelper = new PreprocessingHelper(Properties.stringFromPropertyOrDefault(RUNNABLE_INIT_PREPROCESS_FILE_PROPERTY_NAME,RUNNABLE_INIT_PREPROCESS_FILE_DEFAULT));
	private static PreprocessingHelper callableInitHelper = new PreprocessingHelper(Properties.stringFromPropertyOrDefault(CALLABLE_INIT_PREPROCESS_FILE_PROPERTY_NAME,CALLABLE_INIT_PREPROCESS_FILE_DEFAULT));
	private static PreprocessingHelper forkJoinTaskInitHelper = new PreprocessingHelper(Properties.stringFromPropertyOrDefault(FORKJOINTASK_INIT_PREPROCESS_FILE_PROPERTY_NAME,FORKJOINTASK_INIT_PREPROCESS_FILE_DEFAULT));
	private static PreprocessingHelper executorSubmitHelper = new PreprocessingHelper(Properties.stringFromPropertyOrDefault(EXECUTOR_SUBMIT_PREPROCESS_FILE_PROPERTY_NAME,EXECUTOR_SUBMIT_PREPROCESS_FILE_DEFAULT));


	private GuardsPreprocessing() {
		//Prevents instantiation
	}

	private final static class TaskClassExecGuard {

		@GuardMethod
		public static boolean isApplicable(ReflectionStaticContext rsc) {
			return taskExecHelper.shallClassBeInstrumented(rsc.thisClass());  
		}
	}

	private final static class RunnableClassInitGuard {

		@GuardMethod
		public static boolean isApplicable(ReflectionStaticContext rsc) {
			return runnableInitHelper.shallClassBeInstrumented(rsc.thisClass());  
		}
	}

	private final static class CallableClassInitGuard {

		@GuardMethod
		public static boolean isApplicable(ReflectionStaticContext rsc) {
			return callableInitHelper.shallClassBeInstrumented(rsc.thisClass());  
		}
	}

	private final static class ForkJoinTaskClassInitGuard {

		@GuardMethod
		public static boolean isApplicable(ReflectionStaticContext rsc) {
			return forkJoinTaskInitHelper.shallClassBeInstrumented(rsc.thisClass());  
		}
	}

	private final static class TaskMethodGuard {

		@GuardMethod
		public static boolean isApplicable(MethodStaticContext msc, ReflectionStaticContext rsc) {
			return taskExecHelper.shallMethodBeInstrumented(rsc.thisClass(), msc.thisMethodName() + msc.thisMethodDescriptor().substring(0, 3));
		}
	}

	private final static class RunnableConstructorGuard {

		@GuardMethod
		public static boolean isApplicable(MethodStaticContext msc, ReflectionStaticContext rsc) {
			return runnableInitHelper.shallMethodBeInstrumented(rsc.thisClass(), msc.thisMethodName());
		}
	}

	private final static class CallableConstructorGuard {

		@GuardMethod
		public static boolean isApplicable(MethodStaticContext msc, ReflectionStaticContext rsc) {
			return callableInitHelper.shallMethodBeInstrumented(rsc.thisClass(), msc.thisMethodName());
		}
	}

	private final static class ForkJoinTaskConstructorGuard {

		@GuardMethod
		public static boolean isApplicable(MethodStaticContext msc, ReflectionStaticContext rsc) {
			return forkJoinTaskInitHelper.shallMethodBeInstrumented(rsc.thisClass(), msc.thisMethodName());
		}
	}

	public final static class TaskConstructionGuardRTC {

		private TaskConstructionGuardRTC() { 
			/* Prevents instantiation */ 
		}

		@GuardMethod
		public static boolean isApplicable(final GuardContext gc, final MethodStaticContext msc, ReflectionStaticContext rsc) {

			boolean result = false;

			if (runnableInitHelper.isTargetMethod(msc.thisMethodName()) || 
					callableInitHelper.isTargetMethod(msc.thisMethodName()) || 
					runnableInitHelper.isTargetMethod(msc.thisMethodName())) {

				result = gc.invoke(RunnableClassInitGuard.class) || 
						gc.invoke(CallableClassInitGuard.class) || 
						gc.invoke(ForkJoinTaskClassInitGuard.class);

				if (result == false && ( runnableInitHelper.shallClassBeCheckedAtRuntime(rsc.thisClass()) ||
						callableInitHelper.shallClassBeCheckedAtRuntime(rsc.thisClass()) ||
						forkJoinTaskInitHelper.shallClassBeCheckedAtRuntime(rsc.thisClass())
						)) { 
					return true;
				}
			}

			return false;
		}
	}

	public final static class RunnableConstructionGuard {

		private RunnableConstructionGuard() { 
			/* Prevents instantiation */ 
		}

		@GuardMethod
		public static boolean isApplicable(final GuardContext gc, final MethodStaticContext msc, ReflectionStaticContext rsc) {

			boolean result = false;

			if (runnableInitHelper.isTargetMethod(msc.thisMethodName())) { 
				result = gc.invoke(RunnableClassInitGuard.class) && gc.invoke(RunnableConstructorGuard.class);
			}

			return result;
		}
	}

	public final static class CallableConstructionGuard {

		private CallableConstructionGuard() { 
			/* Prevents instantiation */ 
		}

		@GuardMethod
		public static boolean isApplicable(final GuardContext gc, final MethodStaticContext msc, ReflectionStaticContext rsc) {

			boolean result = false;

			if (callableInitHelper.isTargetMethod(msc.thisMethodName())) {
				result = gc.invoke(CallableClassInitGuard.class) && gc.invoke(CallableConstructorGuard.class);
			}

			return result;
		}
	}

	public final static class ForkJoinTaskConstructionGuard {

		private ForkJoinTaskConstructionGuard() { 
			/* Prevents instantiation */ 
		}

		@GuardMethod
		public static boolean isApplicable(final GuardContext gc, final MethodStaticContext msc, ReflectionStaticContext rsc) {

			boolean result = false;

			if (forkJoinTaskInitHelper.isTargetMethod(msc.thisMethodName())) {

				result = gc.invoke(ForkJoinTaskClassInitGuard.class) && gc.invoke(ForkJoinTaskConstructorGuard.class);
			}

			return result;
		}
	}

	public final static class TaskExecutionGuard {

		private TaskExecutionGuard() { 
			/* Prevents instantiation */ 
		}

		@GuardMethod
		public static boolean isApplicable(final GuardContext gc, final MethodStaticContext msc, ReflectionStaticContext rsc) {

			boolean result = false;

			if (taskExecHelper.isTargetMethod(msc.thisMethodName() + msc.thisMethodDescriptor().substring(0, 3))) {
				result = gc.invoke(TaskClassExecGuard.class) && gc.invoke(TaskMethodGuard.class);

			}

			return result;
		}
	}

	public final static class TaskExecutionGuardRTC {

		private TaskExecutionGuardRTC() { 
			/* Prevents instantiation */ 
		}

		@GuardMethod
		public static boolean isApplicable(final GuardContext gc, final MethodStaticContext msc, ReflectionStaticContext rsc) {

			boolean result = false;

			if (taskExecHelper.isTargetMethod(msc.thisMethodName() + msc.thisMethodDescriptor().substring(0, 3))) {
				result = gc.invoke(TaskClassExecGuard.class);
				if (result == false && taskExecHelper.shallClassBeCheckedAtRuntime(rsc.thisClass())) { 
					return true;
				}
			}

			return false;

		}
	}

	public final static class ExecutorClassGuard {

		@GuardMethod
		public static boolean isApplicable(ReflectionStaticContext rsc) {
			return executorSubmitHelper.shallClassBeInstrumented(rsc.thisClass());
		}
	}

	public final static class ExecutorMethodGuard {

		@GuardMethod
		public static boolean isApplicable(MethodStaticContext msc, ReflectionStaticContext rsc) {
			return executorSubmitHelper.shallMethodBeInstrumented(rsc.thisClass(), msc.thisMethodName() + msc.thisMethodDescriptor().substring(0, Utils.min(21, msc.thisMethodDescriptor().length())));
		}
	}

	public final static class ExecutorSubmitGuard {

		private ExecutorSubmitGuard() { 
			/* Prevents instantiation */ 
		}

		@GuardMethod
		public static boolean isApplicable(final GuardContext gc, final MethodStaticContext msc) {

			boolean result = false;

			if (executorSubmitHelper.isTargetMethod(msc.thisMethodName() + msc.thisMethodDescriptor().substring(0, Utils.min(21, msc.thisMethodDescriptor().length())))) {
				result = gc.invoke(ExecutorClassGuard.class) && gc.invoke(ExecutorMethodGuard.class);
			}

			return result;
		}
	}

	public final static class ExecutorSubmitGuardRTC {

		private ExecutorSubmitGuardRTC() { 
			/* Prevents instantiation */ 
		}

		@GuardMethod
		public static boolean isApplicable(final GuardContext gc, final MethodStaticContext msc, ReflectionStaticContext rsc) {

			boolean result = false;

			if (executorSubmitHelper.isTargetMethod(msc.thisMethodName() + msc.thisMethodDescriptor().substring(0, Utils.min(21, msc.thisMethodDescriptor().length())))) {

				result = gc.invoke(ExecutorClassGuard.class);
				if (result == false && executorSubmitHelper.shallClassBeCheckedAtRuntime(rsc.thisClass())) { 
					return true;
				}
			}

			return false;
		}
	}
}