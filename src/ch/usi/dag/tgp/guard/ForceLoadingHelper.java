package ch.usi.dag.tgp.guard;

import java.util.Collection;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import ch.usi.dag.disl.Reflection;
import ch.usi.dag.disl.Reflection.Class;
import ch.usi.dag.disl.Reflection.ClassLoader;
import ch.usi.dag.disl.Reflection.MissingClassException;

/**
 * <h1>ForceLoadingHelper</h1>
 * This class contains helper methods for determining whether a class falls in the scope of the analysis 
 * (i.e., it should be instrumented) or not. This class should be used in conjunction with the DiSL Reflection API, 
 * when preprocessing reflective supertype information of the Java class library is disabled.  
 */
public class ForceLoadingHelper implements GuardHelper {

	static public class ClassAndLoader {
		private String className;
		private int classloader;

		public String getName() {
			return className;
		}

		public int getClassloader() {
			return classloader;
		}

		public ClassAndLoader(String name, int classloader) {
			this.className = name;
			this.classloader = classloader;
		}

		@Override
		public boolean equals (Object o) {
			if (o instanceof ClassAndLoader) {
				if (
						((ClassAndLoader) o).className.equals(this.className) &&
						((ClassAndLoader) o).classloader == this.classloader) {
					return true;
				}						
			}

			return false;
		}

		@Override
		public int hashCode() {
			int result = 17;
			result = 31 * result + className.hashCode();
			result = 31 * result + classloader;
			return result;

		}

	}

	private class ReturnClass {
		private boolean isMarked = false;
		private boolean runtimeCheck = false;
		private Set<String> targetMethods = new HashSet<>();

		private ReturnClass(boolean marked) {
			isMarked = marked;
		}

		private ReturnClass(boolean marked, boolean runtimeCheck) {
			isMarked = marked;
			this.runtimeCheck = runtimeCheck;
		}

	}

	private Map<ClassAndLoader, Set<String>> whitelistClassesAndMethods;
	private Set<ClassAndLoader> blacklistClasses;
	private final Set<String> targetMethods;
	private Set<ClassAndLoader> whitelistClasses;

	private Map<Class, Boolean> alreadyChecked;	
	private Set<Class> checkAtRuntime;

	private void __addToBlacklist(ClassAndLoader cl) {		
		blacklistClasses.add(cl);
	}

	private void __addToWhitelist(ClassAndLoader cl, Set<String> targetMethods) {
		whitelistClasses.add(cl);		
		whitelistClassesAndMethods.putIfAbsent(cl, targetMethods);
	}

	public ForceLoadingHelper(Map<ClassAndLoader, Set<String>> whitelistClassesAndMethods, Set<ClassAndLoader> blacklistClasses) {

		this.whitelistClassesAndMethods = whitelistClassesAndMethods;
		this.blacklistClasses = blacklistClasses;
		this.whitelistClasses = new HashSet<>();
		this.whitelistClasses.addAll(whitelistClassesAndMethods.keySet());
		this.targetMethods = __flatten(whitelistClassesAndMethods.values());
		this.alreadyChecked = new HashMap<>();
		this.checkAtRuntime = new HashSet<>();
	}

	private Set<String> __flatten(Collection<Set<String>> collection) {
		Set<String> res = new HashSet<>();

		for (Set<String> set: collection) {
			res.addAll(set);
		}

		return res;
	}

	@Override
	public boolean isTargetMethod(String method) {
		return targetMethods.contains(method);
	}

	@Override
	public boolean shallMethodBeInstrumented(Class klass, String method) {		
		if (shallClassBeInstrumented(klass)) {
			ClassAndLoader cal = new ClassAndLoader(klass.internalName(), klass.classLoader().getTag());
			return whitelistClassesAndMethods.get(cal).contains(method);
		}

		return false;
	}

	private Class __getTargetClassFromClassloader(String targetClassName, ClassLoader classloader) {
		Optional<Class> result = classloader.classForInternalName(targetClassName);
		if (result.isPresent()) {
			return result.get();
		}

		return null;
	}

	private List<Class> __getVisibleTargetClasses(Set<ClassAndLoader> targetClasses, ClassLoader classloader, Class klass, ClassAndLoader cc) {

		List<Class> reachableClasses = new LinkedList<>();

		for (ClassAndLoader tc: targetClasses) {
			Class tcClass = __getTargetClassFromClassloader(tc.className, classloader);			
			if (tcClass != null && tcClass.classLoader().getTag() == tc.classloader) {
				reachableClasses.add(tcClass);
			} else {
				if (Reflection.getLoadersOfClass(tc.className).isEmpty()) {					
					checkAtRuntime.add(klass);
				}
			}
		}

		return reachableClasses;
	}

	@SuppressWarnings("unlikely-arg-type")
	private ReturnClass __isSubtypeOfClasses(Class klass,  List<Class> targetClasses, boolean checkMethods) {

		ReturnClass ret = new ReturnClass(false);

		Set<Class> alreadyChecked = new HashSet<>();
		Deque<Class> classesToCheck = new LinkedList<>();
		classesToCheck.addLast(klass);

		while (!classesToCheck.isEmpty()) {

			Class currentClass = classesToCheck.removeFirst();
			alreadyChecked.add(currentClass);

			if (targetClasses.contains(currentClass)) {
				ret.isMarked = true;
				if (checkMethods) {
					ret.targetMethods.addAll(whitelistClassesAndMethods.get(
							new ClassAndLoader(currentClass.internalName(), currentClass.classLoader().getTag())));
				}
			}

			List<Class> supertypes = new LinkedList<>();

			try {
				Optional<Class> superklass = currentClass.superClass();
				Stream<Class> interfaces = currentClass.interfaces();

				if (superklass.isPresent()) {
					supertypes.add(superklass.get());
				}

				supertypes.addAll(interfaces.collect(Collectors.toList()));

			} catch (MissingClassException e) {

				System.err.println("WARNING: supertype of "+currentClass.internalName() + " not found.");
				checkAtRuntime.add(klass);
				System.err.println("WARNING: class "+klass.internalName() + " added to runtime check.");
				return new ReturnClass(false, true); 
			}

			for (Class supertype: supertypes) {

				if (! alreadyChecked.contains(supertypes)) {
					classesToCheck.addLast(supertype);					
				}
			}
		}

		return ret; 
	}

	@Override
	public boolean shallClassBeInstrumented(Class klass) {

		if (alreadyChecked.containsKey(klass)) {
			return alreadyChecked.get(klass);
		}

		ClassAndLoader cc = new ClassAndLoader(klass.internalName(), klass.classLoader().getTag());

		boolean result = false;

		ReturnClass retBlack = __isSubtypeOfBlackClass(klass, cc);

		if (retBlack.runtimeCheck) {
			return false;
		}

		if (retBlack.isMarked) {	
			__addToBlacklist(cc);
		}		
		else { 
			ReturnClass retWhite = __isSubtypeOfWhiteClass(klass, cc);
			if (retWhite.runtimeCheck) {
				return false;
			}

			if (retWhite.isMarked) {
				result = true;
				__addToWhitelist(cc, retWhite.targetMethods);
			}
		}

		alreadyChecked.put(klass, result);
		return result; 

	}

	private ReturnClass __isSubtypeOfClasses(Class klass, ClassAndLoader cc, Set<ClassAndLoader> classes, boolean checkTargetMethods) {

		List<Class> targetClasses = __getVisibleTargetClasses(classes, klass.classLoader(), klass, cc);

		if (targetClasses.isEmpty()) {						
			return new ReturnClass(false);
		}

		return __isSubtypeOfClasses(klass, targetClasses, checkTargetMethods);
	}

	private ReturnClass __isSubtypeOfWhiteClass(Class klass, ClassAndLoader cc) {
		ReturnClass result = __isSubtypeOfClasses(klass, cc, whitelistClasses, true);
		return result;
	}
	private ReturnClass  __isSubtypeOfBlackClass(Class klass, ClassAndLoader cc) {		
		ReturnClass result =  __isSubtypeOfClasses(klass, cc, blacklistClasses, false);
		return result;
	}

	@Override
	public boolean shallClassBeCheckedAtRuntime(Class klass) {
		return checkAtRuntime.contains(klass);
	}
}