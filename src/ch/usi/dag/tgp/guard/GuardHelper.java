package ch.usi.dag.tgp.guard;

/**
 * <h1>GuardHelper</h1>
 */
public interface GuardHelper {

	public boolean isTargetMethod(final String method);	
	public boolean shallMethodBeInstrumented(final ch.usi.dag.disl.Reflection.Class klass, final String method);
	public boolean shallClassBeInstrumented(final ch.usi.dag.disl.Reflection.Class klass);
	public boolean shallClassBeCheckedAtRuntime(final ch.usi.dag.disl.Reflection.Class klass );
}