package ch.usi.dag.tgp.cc;

import java.util.concurrent.Callable;
import java.util.concurrent.Executor;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.ForkJoinTask;
import ch.usi.dag.disl.annotation.After;
import ch.usi.dag.disl.annotation.Before;
import ch.usi.dag.disl.annotation.ThreadLocal;
import ch.usi.dag.disl.dynamiccontext.DynamicContext;
import ch.usi.dag.disl.marker.AfterInitBodyMarker;
import ch.usi.dag.disl.marker.BodyMarker;
import ch.usi.dag.disl.staticcontext.MethodStaticContext;
import ch.usi.dag.tgp.guard.GuardsPreprocessing;
import ch.usi.dag.tgp.util.Stack;
import ch.usi.dag.tgp.util.Utils;

/**
 * <h1>Instrumentation (Calling-context profiling)</h1>
 * This class contains instrumentation code to be inserted in the target application. 
 * The code collects calling contexts upon task creation, submission and execution.
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
	static Stack<String> cc;

	/* ***************************
	 * 		COMMON
	 * ***************************/

	@Before(marker=BodyMarker.class, order=3) 
	public static void beforeAllMethods(MethodStaticContext msc) {
		if (cc == null) {
			cc = new Stack<>();
		}
		cc.push(msc.getUniqueInternalName());
	}

	@After(marker=BodyMarker.class) 
	public static void afterAllMethods() {
		cc.pop();
	}

	/* ***************************
	 * 		INIT CC
	 * ***************************/

	@After(marker = AfterInitBodyMarker.class, guard = GuardsPreprocessing.RunnableConstructionGuard.class, order=2)
	public static void afterRunnableCreation(DynamicContext dc) {
		Local.registerInitCallingContext(dc.getThis(), cc.toString());
	}

	@After(marker = AfterInitBodyMarker.class, guard = GuardsPreprocessing.CallableConstructionGuard.class, order=2)
	public static void afterCallableCreation(DynamicContext dc) {
		Local.registerInitCallingContext(dc.getThis(), cc.toString());
	}

	@After(marker = AfterInitBodyMarker.class, guard = GuardsPreprocessing.ForkJoinTaskConstructionGuard.class, order=2)
	public static void afterForkJoinTaskCreation(DynamicContext dc) {
		Local.registerInitCallingContext(dc.getThis(), cc.toString());
	}

	@After(marker = AfterInitBodyMarker.class, guard = GuardsPreprocessing.TaskConstructionGuardRTC.class)
	public static void afterTaskCreationRTC(DynamicContext dc, MethodStaticContext msc) {
		if (msc.thisMethodName().equals("<init>") && 
				(dc.getThis() instanceof Runnable ||
						dc.getThis() instanceof Callable<?> ||
						dc.getThis() instanceof ForkJoinTask<?>)) {
			Local.registerInitCallingContext(dc.getThis(), cc.toString());
		}
	}

	/* ***************************
	 * 		EXEC CC
	 * ***************************/

	@Before(marker = BodyMarker.class, guard = GuardsPreprocessing.TaskExecutionGuard.class, order=2) 
	public static void beforeExecutionMethod(DynamicContext dc) {
		Local.registerExecCallingContext(dc.getThis(), cc.toString());
	}

	@Before(marker = BodyMarker.class, guard = GuardsPreprocessing.TaskExecutionGuardRTC.class, order=2)
	public static void beforeExecutionMethodRTC(DynamicContext dc, MethodStaticContext msc) {		
		Object thisInstance = dc.getThis();
		String method = msc.thisMethodName() + msc.thisMethodDescriptor().substring(0, 3);
		if ( (thisInstance instanceof Runnable && method.equals("run()V")) ||
				(thisInstance instanceof Callable<?> && method.equals("call()L")) ||
				(thisInstance instanceof ForkJoinTask<?> && method.equals("exec()Z"))
				){  

			Local.registerExecCallingContext(dc.getThis(), cc.toString());
		}
	}

	/* ***************************
	 * 		SUBMIT CC
	 * ***************************/

	@Before(marker = BodyMarker.class, guard = GuardsPreprocessing.ExecutorSubmitGuard.class) 
	public static void beforeSubmissionMethod(DynamicContext dc) {
		Local.registerSubmitCallingContext(dc.getMethodArgumentValue(0, Object.class), cc.toString());
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
			Local.registerSubmitCallingContext(dc.getMethodArgumentValue(0, Object.class), cc.toString());
		}
	}
}