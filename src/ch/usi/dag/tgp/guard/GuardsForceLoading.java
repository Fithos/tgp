package ch.usi.dag.tgp.guard;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import ch.usi.dag.disl.annotation.GuardMethod;
import ch.usi.dag.disl.guardcontext.GuardContext;
import ch.usi.dag.disl.guardcontext.ReflectionStaticContext;
import ch.usi.dag.disl.staticcontext.MethodStaticContext;
import ch.usi.dag.tgp.guard.ForceLoadingHelper.ClassAndLoader;
import ch.usi.dag.tgp.util.Utils;

/**
 * <h1>GuardsForceLoading</h1>
 * This class contains guards that use the DiSL Reflection API, without using preprocessed reflective supertype information of the Java class library. 
 */
public class GuardsForceLoading {


	private static ForceLoadingHelper taskExecHelper = __initTaskExecHelper();
	private static ForceLoadingHelper runnableInitHelper = __initRunnableInitHelper();
	private static ForceLoadingHelper callableInitHelper = __initCallableInitHelper();
	private static ForceLoadingHelper forkJoinTaskInitHelper = __initForkJoinTaskInitHelper();
	private static ForceLoadingHelper executorSubmitHelper = __initExecutorSubmitHelper();


	private GuardsForceLoading() {
		//Prevents instantation
	}

	private static ForceLoadingHelper __initRunnableInitHelper() {

		Set<ClassAndLoader> blacklist = new HashSet<>();
		Map<ClassAndLoader, Set<String>> whitelist = new HashMap<>();

		Set<String> methods = new HashSet<>();
		methods.add("<init>");
		whitelist.put(new ClassAndLoader("java/lang/Runnable",0), methods);

		return new ForceLoadingHelper(whitelist, blacklist);

	}

	private static ForceLoadingHelper __initCallableInitHelper() {

		Set<ClassAndLoader> blacklist = new HashSet<>();
		Map<ClassAndLoader, Set<String>> whitelist = new HashMap<>();

		Set<String> methods = new HashSet<>();
		methods.add("<init>");
		whitelist.put(new ClassAndLoader("java/util/concurrent/Callable",0), methods);

		return new ForceLoadingHelper(whitelist, blacklist);

	}

	private static ForceLoadingHelper __initForkJoinTaskInitHelper() {

		Set<ClassAndLoader> blacklist = new HashSet<>();
		Map<ClassAndLoader, Set<String>> whitelist = new HashMap<>();

		Set<String> methods = new HashSet<>();
		methods.add("<init>");
		whitelist.put(new ClassAndLoader("java/util/concurrent/ForkJoinTask",0), methods);

		return new ForceLoadingHelper(whitelist, blacklist);

	}

	private static ForceLoadingHelper __initTaskExecHelper() {

		Set<ClassAndLoader> blacklist = new HashSet<>();
		Map<ClassAndLoader, Set<String>> whitelist = new HashMap<>();

		Set<String> run = new HashSet<>();
		run.add("run()V");
		whitelist.put(new ClassAndLoader("java/lang/Runnable",0), run);

		Set<String> call = new HashSet<>();
		call.add("call()L");
		whitelist.put(new ClassAndLoader("java/util/concurrent/Callable",0), call);

		Set<String> exec = new HashSet<>();
		exec.add("exec()Z");
		whitelist.put(new ClassAndLoader("java/util/concurrent/ForkJoinTask",0), exec);

		return new ForceLoadingHelper(whitelist, blacklist);

	}

	private static ForceLoadingHelper __initExecutorSubmitHelper() {

		Set<ClassAndLoader> blacklist = new HashSet<>();			
		Map<ClassAndLoader, Set<String>> whitelist = new HashMap<>();

		Set<String> submit = new HashSet<>();
		submit.add("submit(Ljava/util/concurren");
		submit.add("submit(Ljava/lang/Runnable;");			
		whitelist.put(new ClassAndLoader("java/util/concurrent/ExecutorService",0), submit);

		Set<String> execute = new HashSet<>();
		execute.add("execute(Ljava/lang/Runnable;");
		whitelist.put(new ClassAndLoader("java/util/concurrent/Executor",0), execute);

		return new ForceLoadingHelper(whitelist, blacklist);

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

			if (runnableInitHelper.isTargetMethod(msc.thisMethodName())) { //Descriptor NOT included
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