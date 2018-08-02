package ch.usi.dag.tgp.util;

import java.io.IOException;
import java.io.PrintWriter;
import java.nio.charset.Charset;
import java.nio.file.FileSystems;
import java.nio.file.Files;
import java.nio.file.OpenOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

/**
 * <h1>CSVDumper</h1>
 * A class to ease metric dumping in a CSV file.
 */ 
public class CSVDumper {

	private static final String PREFIX_PROPERTY_NAME = "tgp.csvdumper.prefix";
	private static final String SUFFIX_PROPERTY_NAME = "tgp.csvdumper.suffix";
	private static final String HEADER_PRINT_PROPERTY_NAME = "tgp.csvdumper.printheader";
	private static final String HEADER_PRINT_DEFAULT= "true";
	private static final String APPEND_FILE_PROPERTY_NAME = "tgp.csvdumper.append";
	private static final String APPEND_FILE_DEFAULT= "false";

	private static final String PREFIX_HEADER_PROPERTY_NAME = "tgp.csvdumper.prefixheader";	
	private static final String SUFFIX_HEADER_PROPERTY_NAME = "tgp.csvdumper.suffixheader";

	private static final OpenOption[] fileOptionsNormal = {StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING, StandardOpenOption.WRITE};
	private static final OpenOption[] fileOptionsAppend = {StandardOpenOption.CREATE, StandardOpenOption.APPEND, StandardOpenOption.WRITE};

	public class CSVDumperException extends Exception {

		public CSVDumperException(String string) {
			super(string);
		}

		private static final long serialVersionUID = -4954253064093442866L;

	}

	private PrintWriter outputWriter;
	private int nColumns;
	private String formatString;
	private String sep = ","; 
	private boolean fileClosed;

	public CSVDumper(String filePath) {
		try {
			__initializeMetricFile(filePath);
		} catch (IOException e) {
			System.err.println("[Error] Failed to create file: " + e.getMessage());
		}
	}

	public CSVDumper(String filePath, String... header) {		
		this(filePath);		
		__printHeader(header);		
	}

	private void __printHeader(String... header) {
		if (Properties.stringFromPropertyOrDefault(HEADER_PRINT_PROPERTY_NAME,HEADER_PRINT_DEFAULT).equals("true")) {
			__dumpHeader(header);
		}
	}

	private void __initializeMetricFile(String filePath) throws IOException {
		Path path = FileSystems.getDefault().getPath(filePath);
		Path dirs = path.getParent();
		if (!Files.exists(dirs)) {
			Files.createDirectories(dirs);
		}

		outputWriter = new PrintWriter(Files.newBufferedWriter(path, Charset.defaultCharset(), __determineOpenOptions()));	
		fileClosed = false;
	}

	private OpenOption[] __determineOpenOptions() {
		if (Properties.stringFromPropertyOrDefault(APPEND_FILE_PROPERTY_NAME, APPEND_FILE_DEFAULT).equals("true")) {
			return fileOptionsAppend;
		}

		return fileOptionsNormal;
	}

	public void dumpLine(String... items) {
		__checkAccess(); 
		try { 
			__handleColumn(items);	
			__handleFormat(items);					
			outputWriter.print(String.format(formatString,(Object[]) items));
		} catch (CSVDumperException e) {
			System.err.println(e.getMessage());
		}
	}

	private void __dumpHeader(String... header) {
		__checkAccess(); 
		try { 
			__handleColumn(header);						
			outputWriter.print(String.format(__createHeaderFormatString(header),(Object[]) header));
		} catch (CSVDumperException e) {
			System.err.println(e.getMessage());
		}
	}

	private void __handleColumn(String... items) throws CSVDumperException {

		if (items == null || items.length <=0) {
			throw new CSVDumperException("No item to print!");
		}

		if (nColumns != 0 && items.length != nColumns) {
			throw new CSVDumperException("Attempting to print a different number of columns than a line already printed!");
		}

		if (nColumns == 0) {
			nColumns = items.length;
		}

	}

	private void __handleFormat(String... items) throws CSVDumperException {
		if (formatString == null) {

			StringBuilder str = new StringBuilder();

			str.append(__stringFromProperty(PREFIX_PROPERTY_NAME));


			for (int i = 0; i < items.length; i++) {
				str.append("%s"+sep);				
			}												

			str.append(__stringFromProperty(SUFFIX_PROPERTY_NAME));
			str.deleteCharAt(str.length()-1); 
			str.append("\n");
			formatString = str.toString();
		}				

	}

	private String __createHeaderFormatString(String... header) {
		StringBuilder str = new StringBuilder();

		str.append(__stringFromProperty(PREFIX_HEADER_PROPERTY_NAME));

		for (int i = 0; i < header.length; i++) {
			str.append("%s"+sep);				
		}												

		str.append(__stringFromProperty(SUFFIX_HEADER_PROPERTY_NAME));
		str.deleteCharAt(str.length()-1);
		str.append("\n");

		return str.toString();
	}

	private String __stringFromProperty(String propertyName) {
		String property = Properties.stringFromProperty(propertyName);
		return property != null ? property + sep : "";
	}

	public void closeFile() {
		__checkAccess(); 
		outputWriter.close();
		fileClosed = true;
	}

	private void __checkAccess() {
		if (fileClosed) {
			throw new IllegalAccessError("Trace already closed!");
		}
	}
}