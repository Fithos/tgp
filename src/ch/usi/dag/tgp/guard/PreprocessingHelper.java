package ch.usi.dag.tgp.guard;

import java.io.IOException;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import ch.usi.dag.typeparser.Exceptions.UnknownSupertypeException;
import ch.usi.dag.typeparser.IOReflectionHelper;
import ch.usi.dag.typeparser.TypeGraph;
import ch.usi.dag.typeparser.TypeParserConfig;

/**
 * <h1>PreprocessingHelper</h1>
 * This class contains helper methods for determining whether a class falls in the scope of the analysis 
 * (i.e., it should be instrumented) or not. This class should be used in conjunction with the DiSL Reflection API, 
 * when preprocessing reflective supertype information of the Java class library is enabled. 
 */

public class PreprocessingHelper implements GuardHelper {

	private TypeGraph<DiSLReflectionType> graph;
	private Map<ch.usi.dag.disl.Reflection.Class, DiSLReflectionType> classToTypeMap = new HashMap<>();
	private Set<String> targetMethods;
	private Set<ch.usi.dag.disl.Reflection.Class> checkAtRuntime = new HashSet<>();
	private TypeParserConfig config;
	private IOReflectionHelper ioHelper;

	public PreprocessingHelper(final IOReflectionHelper helper, final String inputFile) {
		this.ioHelper = helper;
		this.config = TypeParserConfig.getInstance();
		config.inputTypeGraphFile = inputFile;
		__loadGraph();
	}

	public PreprocessingHelper(final String inputFile) {
		this.ioHelper = new IOReflectionHelper();
		this.config = TypeParserConfig.getInstance();
		config.inputTypeGraphFile = inputFile;
		__loadGraph();
	}

	@SuppressWarnings("unchecked")
	private void __loadGraph() {

		if (graph == null) {
			try {
				graph = (TypeGraph<DiSLReflectionType>) ioHelper.importTypeGraph();
			} catch (ClassNotFoundException e) {
				System.err.println("Error: class TypeGraph not found. The JVM environment is broken.");
				e.printStackTrace();
			} catch (IOException e) {
				System.err.println("Error: exception while reading file. ");
				e.getMessage();				
				e.printStackTrace();
			}	
			targetMethods = graph.getWhiteList().getAllAttributes();
		}
	}

	public boolean isTargetMethod(final String method) {
		return targetMethods.contains(method);
	}

	private DiSLReflectionType __createOrGetDislReflectionType(final ch.usi.dag.disl.Reflection.Class klass) {

		DiSLReflectionType dislType;

		if (classToTypeMap.containsKey(klass)) {
			dislType = classToTypeMap.get(klass);
			if (!dislType.isDiSLClassSet()) {
				dislType.setDiSLClass(klass);
			}
			return dislType;
		}

		dislType = new DiSLReflectionType(klass);
		classToTypeMap.put(klass, dislType);
		return dislType;
	}

	public boolean shallClassBeCheckedAtRuntime(final ch.usi.dag.disl.Reflection.Class klass ) {
		return checkAtRuntime.contains(klass);
	}

	public boolean shallMethodBeInstrumented(final ch.usi.dag.disl.Reflection.Class klass, final String method) {

		Set<String> targetMethodsOfType = graph.getAttributesIfWhite(__createOrGetDislReflectionType(klass));
		if (targetMethodsOfType != null ) {
			if (targetMethodsOfType.contains(method)) {
				return true;
			}
		}			
		return false;
	}

	public boolean shallClassBeInstrumented(final ch.usi.dag.disl.Reflection.Class klass) {

		DiSLReflectionType dislType = __createOrGetDislReflectionType(klass);

		if (graph.isPresent(dislType)) {
			if (graph.isWhite(dislType)) {				
				return true;
			}
			return false;
		}

		try {
			graph.addType(dislType);				
		} catch (UnknownSupertypeException e) {
			System.err.println("WARNING! Impossible to find supertypes of " + e.getType().getName());
			checkAtRuntime.add(klass);
			return false;
		}

		if (graph.isWhite(dislType)) {
			return true;
		}
		return false;
	}

	public void exportData() throws IOException {
		ioHelper.exportAll(graph);

	}
}