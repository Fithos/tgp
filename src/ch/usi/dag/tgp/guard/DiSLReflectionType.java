package ch.usi.dag.tgp.guard;

import java.io.Serializable;
import java.util.HashSet;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;
import ch.usi.dag.disl.Reflection.MissingClassException;
import ch.usi.dag.typeparser.AbstractType;
import ch.usi.dag.typeparser.Exceptions.UnknownSupertypeException;

/**
 * <h1>DiSLReflectionType</h1>
 * The purpose of this class is to represent a type to be inserted into a TypeGraph. 
 * This class has been designed to try several ways for getting the supertypes of the type it represents. In particular, the class can: <br>
 *    
 * 1) Store the names of the supertypes directly as String provided by the user. In this way, method getSupertypes can never fail (i.e., can
 *  never throw {@link UnknownSupertypeException}). On the other hand, this requires the user (acting as an oracle) to provide the names of the supertypes 
 *  with some external trusted source of information.   <br>
 * 2) Obtain the supertypes with the support of java.lang.Class. This option requires that the JVM in which this DiSLReflectionType
 * is running can load a java.lang.Class corresponding to this type.  <br>
 * 3) Obtain the supertypes with the support of ch.usi.dag.disl.Reflection.Class. This option activates the 
 * force-loading mechanism of DiSL, asking the target JVM to force-load the supertypes of this type and send their definitions 
 * (encapsulated in a ch.usi.dag.disl.Reflection.Class) to this JVM. <br>
 * 
 *    The rationale of supporting several ways of getting the supertypes is to minimize the failures of the getSupertypes()
 *    method. In particular, when the supertypes are requested, the class attempts to find them using all 
 *    the three methods outlined above, in order. 
 *    Only if all of them fail, then a {@link UnknownSupertypeException} is thrown.     
 *       
 */
public class DiSLReflectionType extends AbstractType{

	private static final long serialVersionUID = -6927714905719146881L;

	private transient ch.usi.dag.disl.Reflection.Class classDisl = null;
	private transient Class<?> classJava = null;
	private DiSLReflectionType superClass = null;	
	private boolean superClassHasBeenSet = false;
	private Set<DiSLReflectionType> interfaces = null; 	

	private static int __determineLoader(String classname, int oldLoader) {
		if (classname.startsWith("java/"))	 { 
			return BOOTSTRAP_CLASSLOADER;
		}

		return oldLoader;
	}

	private static String __replaceDotsWithSlashes(String oldString) {
		return oldString.replace('.', '/');
	}

	public DiSLReflectionType(final ch.usi.dag.disl.Reflection.Class klass) {
		super(klass.internalName(), __determineLoader(klass.internalName(), klass.classLoader().getTag()));
		this.classDisl = klass;		
	}

	private DiSLReflectionType(final Class<?> klass, int classloader) {
		super(__replaceDotsWithSlashes(klass.getName()), __determineLoader(__replaceDotsWithSlashes(klass.getName()), classloader));
		this.classJava = klass;	
	}

	public boolean isDiSLClassSet() {
		return classDisl != null;
	}

	public void setDiSLClass(final ch.usi.dag.disl.Reflection.Class klass) {
		if (classDisl != null) {
			throw new IllegalAccessError();
		}

		this.classDisl = klass;		
	}

	/**
	 * Determine the interfaces implemented or extended by this type.  
	 * The contract for this method is the following:  <br>
	 *    a) If this type represents java.lang.Object, an empty set is returned<br>
	 *    b) If this type represents a class different from java.lang.Object, all interfaces 
	 *    implemented by the class (if any) are returned<br>
	 *    c) If this type represents an interface, all interfaces extended by the interface (if any) 
	 *    are returned<br>
	 *    d) If this type represents a primitive type (including void), the empty set is returned<br>
	 *    e) If this type represents an array, java.lang.Cloneable and java.io.Serializable are returned<br>
	 * <p>
	 *     If, for any reason, it is impossible to determine the FULL set of interfaces implemented or extended by this type, 
	 *     the method throws UnknownSupertypeException.  
	 *     
	 * @throws UnknownSupertypeException if any of the interfaces extended/implemented by this type cannot be determined     
	 * @return a Set of DiSLReflectionTypes, each of them representing an interface implemented/extended by this type
	 */	
	public Set<DiSLReflectionType> getInterfaces() throws UnknownSupertypeException {

		if (interfaces == null) {

			interfaces = new HashSet<>();

			if (__determineInterfacesWithJavaClass()) {
				return interfaces;
			}

			if (__determineInterfacesWithDiSLClass()) {
				return interfaces;
			}

			throw new UnknownSupertypeException(this);
		}

		return interfaces;
	}

	private boolean __determineInterfacesWithJavaClass() {

		if (classJava == null) {
			classJava = __getJavaClass();
		}

		if (classJava == null) {
			return false;
		}

		Class<?>[] interfaces = classJava.getInterfaces();

		for (Class<?> i : interfaces) {
			this.interfaces.add(new DiSLReflectionType(i, super.getClassloader()));
		}

		return true;
	}

	private Class<?> __getJavaClass() {

		Class<?> kl;

		try {
			kl = Class.forName(getName());			
		} catch (ClassNotFoundException e) {
			return null;
		}

		return kl;
	}

	private boolean __determineSuperClassWithDiSLClass() {

		if (classDisl == null) {
			return false;
		}

		if (classDisl.isInterface() || classDisl.isPrimitive() || classDisl.isArray()) {
			this.superClass = new DiSLReflectionType(Object.class, BOOTSTRAP_CLASSLOADER);
			return true;
		}

		Optional<ch.usi.dag.disl.Reflection.Class> result;

		try {		
			result = classDisl.superClass();
		} catch (MissingClassException e) {
			return false;
		}

		if (result.isPresent()) {
			this.superClass = new DiSLReflectionType(result.get());
		}

		return true;
	}

	private boolean __determineInterfacesWithDiSLClass() {

		if (classDisl == null) {
			return false;
		}

		if (classDisl.isPrimitive()) {
			return true;
		}

		if (classDisl.isArray()) {
			this.interfaces.add(new DiSLReflectionType(Cloneable.class, BOOTSTRAP_CLASSLOADER));
			this.interfaces.add(new DiSLReflectionType(Serializable.class, BOOTSTRAP_CLASSLOADER));
			return true;
		}

		Set<ch.usi.dag.disl.Reflection.Class> ints; 

		try {		
			ints = classDisl.interfaces().collect(Collectors.toSet());

		} catch (MissingClassException e) {
			return false;
		}

		for (ch.usi.dag.disl.Reflection.Class i : ints) {
			this.interfaces.add(new DiSLReflectionType(i));
		}

		return true;
	}

	private boolean __determineSuperClassWithJavaClass() {

		if (classJava == null) {
			classJava = __getJavaClass();
		}

		if (classJava == null) {
			return false;
		}

		Class<?> sc = classJava.getSuperclass();

		if (sc == null && !classJava.equals(Object.class)) {
			sc = Object.class;
		}

		DiSLReflectionType superklass = new DiSLReflectionType(sc, super.getClassloader());
		this.superClass = superklass;
		this.superClassHasBeenSet = true;

		return true;
	}

	/** 
	 * Determines the superclass of this type, according to the following contract: 
	 * <p>
	 *    a) If this type represents java.lang.Object, null is returned <br>
	 *    b) If this type represents a class different then java.lang.Object, its superclass is returned<br>
	 *    c) If this type represents an interface, java.lang.Object is returned<br>
	 *    d) If this type represents a primitive type (including void), java.lang.Object is returned<br>
	 *    e) If this type represents an array, java.lang.Object is returned<br>
	 *<p>
	 *		
	 *     If, for any reason, it is impossible to determine the superclass of this type, 
	 *     the method throws UnknownSupertypeException.     
	 * 
	 * @throws UnknownSupertypeException if the superclass of this type cannot be determined
	 * @return a DiSLReflectionType representing the superclass of this type
	 * 
	 */
	public DiSLReflectionType getSuperclass() throws UnknownSupertypeException {

		if (! superClassHasBeenSet) {

			if (getName().equals("java.lang.Object")) {
				superClassHasBeenSet = true;
				return null;
			}

			if (__determineSuperClassWithJavaClass()) {
				return superClass;
			}

			if (__determineSuperClassWithDiSLClass()) {
				return superClass;
			}

			throw new UnknownSupertypeException(this);
		}

		return superClass;
	}

	@Override
	public Set<? extends AbstractType> getSupertypes() throws UnknownSupertypeException {

		Set<DiSLReflectionType> set = new HashSet<>();
		DiSLReflectionType superclass = (DiSLReflectionType) getSuperclass();

		if (superclass != null) {
			set.add(superclass);
		}

		set.addAll(getInterfaces());
		return set;
	}
}