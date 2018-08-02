package ch.usi.dag.tgp.task.hpc;

import java.util.concurrent.Callable;
import java.util.concurrent.Executor;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.ForkJoinTask;
import ch.usi.dag.disl.annotation.After;
import ch.usi.dag.disl.annotation.Before;
import ch.usi.dag.disl.annotation.SyntheticLocal;
import ch.usi.dag.disl.annotation.ThreadLocal;
import ch.usi.dag.disl.dynamiccontext.DynamicContext;
import ch.usi.dag.disl.marker.BodyMarker;
import ch.usi.dag.disl.marker.AfterInitBodyMarker;
import ch.usi.dag.disl.staticcontext.MethodStaticContext;
import ch.usi.dag.tgp.guard.GuardsPreprocessing;
import ch.usi.dag.tgp.task.Local;
import ch.usi.dag.tgp.util.Utils;
import cz.cuni.mff.d3s.perf.MultiContextBenchmark;

/**
 * <h1>Instrumentation (Reference-cycles count)</h1>
 * This class contains instrumentation code to be inserted in the target application. 
 * The code profiles task granularity, representing it in terms of reference-cycle count.
 * <p>
 * <b>Note</b>: Some methods are implemented in two variants. The first resorts to the DiSL Reflection API for querying reflective supertype information 
 * of the class under instrumentation. The second uses runtime type checks, i.e., the instanceof operator, to detect subtypes of task interfaces and task execution frameworks.
 * The second variant can be recognized by the "RTC" suffix. 
 * The first implementation is more efficient, but requires the availability of the DiSL Reflection API. 
 * The second variant is less efficient but can always can be performed.
 * <br>
 * The guards implemented in tgp ensure that, if the DiSL Reflection API is available, the first variant is inserted in the target application.
 * Only if the DiSL Reflection API is unavailable, or if reflective supertype information of the class under instrumentation 
 * is not available in the DiSL server (for any reason), the second variant is inserted in the target application.   
 */
public class Instrumentation {

	@ThreadLocal
	static long rc = 0;

	@ThreadLocal
	static long c_nested_thread = 0;

	@ThreadLocal
	static int tasks_tl = 0;

	@SyntheticLocal
	static int tasks_sl;

	@SyntheticLocal
	static long c_entry_sl;

	@SyntheticLocal
	static long c_nested_outer_sl;

	@SyntheticLocal
	static long times_sl;


	/* *********************
	 *    	TASKS
	 * *********************/

	@After(marker = AfterInitBodyMarker.class, guard = GuardsPreprocessing.RunnableConstructionGuard.class)
	public static void afterRunnableCreation(DynamicContext dc) {
		Local.registerCreation(dc.getThis(), Thread.currentThread(), Local.RUNNABLE_ID);
	}

	@After(marker = AfterInitBodyMarker.class, guard = GuardsPreprocessing.CallableConstructionGuard.class)
	public static void afterCallableCreation(DynamicContext dc) {
		Local.registerCreation(dc.getThis(), Thread.currentThread(), Local.CALLABLE_ID);
	}

	@After(marker = AfterInitBodyMarker.class, guard = GuardsPreprocessing.ForkJoinTaskConstructionGuard.class)
	public static void afterForkJoinTaskCreation(DynamicContext dc) {
		Local.registerCreation(dc.getThis(), Thread.currentThread(), Local.FORKJOINTASK_ID);
	}

	@After(marker = AfterInitBodyMarker.class, guard = GuardsPreprocessing.TaskConstructionGuardRTC.class)
	public static void afterTaskCreationRTC(DynamicContext dc, MethodStaticContext msc) {
		if (msc.thisMethodName().equals("<init>")) {		
			Object thisInstance = dc.getThis();  
			if (thisInstance instanceof Runnable) {
				Local.registerCreation(thisInstance, Thread.currentThread(), Local.RUNNABLE_ID);
			}

			if (thisInstance instanceof Callable<?>) {
				Local.registerCreation(thisInstance, Thread.currentThread(), Local.CALLABLE_ID);
			}

			if (thisInstance instanceof ForkJoinTask<?>) {
				Local.registerCreation(thisInstance, Thread.currentThread(), Local.FORKJOINTASK_ID);
			}
		}
	}

	@Before(marker = BodyMarker.class, guard = GuardsPreprocessing.TaskExecutionGuard.class)
	public static void beforeExecutionMethod(DynamicContext dc) {

		if (rc == 0) {
			rc = Local.createPAPIcontext();
		}

		tasks_sl = tasks_tl;
		tasks_tl = System.identityHashCode(dc.getThis());
		c_nested_outer_sl = c_nested_thread;
		times_sl = System.nanoTime();
		c_entry_sl = MultiContextBenchmark.read(rc)[0];
	}

	@Before(marker = BodyMarker.class, guard = GuardsPreprocessing.TaskExecutionGuardRTC.class)
	public static void beforeExecutionMethodRTC(DynamicContext dc, MethodStaticContext msc) {
		Object thisInstance = dc.getThis();
		String method = msc.thisMethodName() + msc.thisMethodDescriptor().substring(0, 3);
		if ( (thisInstance instanceof Runnable && method.equals("run()V")) ||
				(thisInstance instanceof Callable<?> && method.equals("call()L")) ||
				(thisInstance instanceof ForkJoinTask<?> && method.equals("exec()Z"))
				){  

			if (rc == 0) {
				rc = Local.createPAPIcontext();
			}

			tasks_sl = tasks_tl;
			tasks_tl = System.identityHashCode(dc.getThis());
			c_nested_outer_sl = c_nested_thread;
			times_sl = System.nanoTime();
			c_entry_sl = MultiContextBenchmark.read(rc)[0];
		}
	}

	@After(marker = BodyMarker.class, guard = GuardsPreprocessing.TaskExecutionGuard.class)
	public static void afterExecutionMethod(DynamicContext dc, MethodStaticContext msc) {

		if (rc == 0) {
			rc = Local.createPAPIcontext();
		}

		final long c_nested_task = c_nested_thread - c_nested_outer_sl;

		final long c_current = MultiContextBenchmark.read(rc)[0] - c_entry_sl - c_nested_task;

		if (tasks_sl == 0) {
			Local.registerExecution(dc.getThis(), tasks_tl, 0, c_current, times_sl, System.nanoTime(), Thread.currentThread(), msc.thisMethodName());
			c_nested_thread = 0;			
		}  else if (tasks_sl != tasks_tl) {
			Local.registerExecution(dc.getThis(), tasks_tl, tasks_sl, c_current, times_sl, System.nanoTime(), Thread.currentThread(), msc.thisMethodName());
			c_nested_thread += c_current;
		}

		tasks_tl = tasks_sl;
	}

	@After(marker = BodyMarker.class, guard = GuardsPreprocessing.TaskExecutionGuardRTC.class) 
	public static void afterExecutionMethodRTC(DynamicContext dc, MethodStaticContext msc) {

		Object thisInstance = dc.getThis();
		String method = msc.thisMethodName() + msc.thisMethodDescriptor().substring(0, 3);
		if ( (thisInstance instanceof Runnable && method.equals("run()V")) ||
				(thisInstance instanceof Callable<?> && method.equals("call()L")) ||
				(thisInstance instanceof ForkJoinTask<?> && method.equals("exec()Z"))
				){  

			if (rc == 0) {
				rc = Local.createPAPIcontext();
			}

			final long c_nested_task = c_nested_thread - c_nested_outer_sl;

			final long c_current = MultiContextBenchmark.read(rc)[0] - c_entry_sl - c_nested_task;

			if (tasks_sl == 0) {
				Local.registerExecution(dc.getThis(), tasks_tl, 0, c_current, times_sl, System.nanoTime(), Thread.currentThread(), msc.thisMethodName());
				c_nested_thread = 0;			
			}  else if (tasks_sl != tasks_tl) {
				Local.registerExecution(dc.getThis(), tasks_tl, tasks_sl, c_current, times_sl, System.nanoTime(), Thread.currentThread(), msc.thisMethodName());
				c_nested_thread += c_current;
			}

			tasks_tl = tasks_sl;
		}
	}

	/* *******************************
	 *   TASK EXECUTION FRAMEWORKS
	 * *******************************/

	@Before(marker = BodyMarker.class, guard = GuardsPreprocessing.ExecutorSubmitGuard.class)
	public static void beforeSubmissionMethod(DynamicContext dc) {
		Local.registerSubmission(dc.getMethodArgumentValue(0, Object.class), dc.getThis());
	}

	@Before(marker = BodyMarker.class, guard = GuardsPreprocessing.ExecutorSubmitGuardRTC.class)
	public static void beforeSubmissionMethodRTC(DynamicContext dc, MethodStaticContext msc) {

		Object o = dc.getThis();
		String method = msc.thisMethodName() + msc.thisMethodDescriptor().substring(0, Utils.min(21, msc.thisMethodDescriptor().length()));

		boolean cond1 = o instanceof ExecutorService && 
				(method.equals("submit(Ljava/util/concurren") ||
						method.equals("submit(Ljava/lang/Runnable;") );									
		boolean cond2 = o instanceof Executor && method.equals("execute(Ljava/lang/Runnable;");

		if (cond1 || cond2) {				
			Local.registerSubmission(dc.getMethodArgumentValue(0, Object.class), o);
		}
	}
}