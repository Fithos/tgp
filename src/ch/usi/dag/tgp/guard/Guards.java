package ch.usi.dag.tgp.guard;

import ch.usi.dag.disl.annotation.GuardMethod;
import ch.usi.dag.disl.staticcontext.MethodStaticContext;
import ch.usi.dag.tgp.util.Utils;

/**
 * <h1>Guards</h1>
 * This class contains guards that do not use the DiSL Reflection API. 
 */
public class Guards {

	private Guards() {
		//Prevents instantiation from outside
	}

	public final static class TaskExecutionMethod {

		@GuardMethod
		public static boolean isApplicable(MethodStaticContext msc) {

			String methodName = msc.thisMethodName() + msc.thisMethodDescriptor().substring(0, 3);

			if (methodName.equals("run()V") || methodName.equals("call()L") || methodName.equals("exec()Z")) {
				return true;
			}

			return false;
		}
	}

	public final static class TaskSubmissionMethod {

		@GuardMethod
		public static boolean isApplicable(MethodStaticContext msc) {

			String methodName = msc.thisMethodName() + msc.thisMethodDescriptor().substring(0, Utils.min(21, msc.thisMethodDescriptor().length()));

			if (methodName.equals("submit(Ljava/util/concurren") || methodName.equals("submit(Ljava/lang/Runnable;") || methodName.equals("execute(Ljava/lang/Runnable;")) {
				return true;
			}

			return false;
		}
	}
}