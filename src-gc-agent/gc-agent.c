#include <stdlib.h>
#include <time.h>
#include <sys/time.h>
#include "jvmti.h"
#include <jni.h>

#define GC_TRACE_PATH "profiles/gc.csv"

/*
* NAME: printGCTime
* DESC: prints a timestamp related to a GC event 
* ARGS: type - the type of GC event
*/
void printGCTime(const char* type) {

	  struct timespec spec5;
	  clock_gettime(CLOCK_MONOTONIC, &spec5 );

	//Prints a timestamp equivalent to the method System.nanotime() in Java.
	FILE *f = fopen(GC_TRACE_PATH, "ab+");
	fprintf(f, "%s,%ld\n", type, (spec5.tv_sec * (1000 * 1000 * 1000)  + spec5.tv_nsec));
	fclose(f);

}

/*
* NAME: garbageCollectionStart
* DESC: prints timestamp of GC activation. This method is called when a garbage collection pause begins.
* ARGS: jvmti_env - the pointer to the JVMTI interface 
*/
void JNICALL
garbageCollectionStart(jvmtiEnv *jvmti_env) {

	printGCTime("Start GC");

}

/*
* NAME: garbageCollectionFinish
* DESC: prints timestamp of GC activation. This method is called when a garbage collection pause ends.
* ARGS: jvmti_env - the pointer to the JVMTI interface
*/
void JNICALL
garbageCollectionFinish(jvmtiEnv *jvmti_env) {

	printGCTime("End GC");

}

/*
* NAME: Agent_OnLoad
* DESC: checks whether the JVMTI agent can support notification of GC start and finish
* ARGS: jvm - a pointer to the reference JVM
*       options 
*       reserved
* RETURN: integer (macro) indicating the JVMTI capability to support notification of event
*         JVMTI_ERROR_UNSUPPORTED_VERSION - JVMTI version not supported
*         JVMTI_ERROR_OUT_OF_MEMORY - JVMTI does not have enough memory
*         JVMTI_ERROR_NONE - no error occurred
* ERRORS: exits with -1 
*/
JNIEXPORT jint JNICALL
Agent_OnLoad(JavaVM * jvm, char *options, void *reserved)
{
	jvmtiEnv *jvmti_env;

	jint returnCode = (*jvm)->GetEnv(jvm, (void **) &jvmti_env,
			JVMTI_VERSION_1_0);



	if (returnCode != JNI_OK)
	{
		fprintf(stderr,
				"The version of JVMTI requested (1.0) is not supported by this JVM.\n");
		return JVMTI_ERROR_UNSUPPORTED_VERSION;
	}


	jvmtiCapabilities *requiredCapabilities;

	requiredCapabilities = (jvmtiCapabilities*) calloc(1, sizeof(jvmtiCapabilities));
	if (!requiredCapabilities)
	{
		fprintf(stderr, "Unable to allocate memory\n");
		return JVMTI_ERROR_OUT_OF_MEMORY;
	}

	requiredCapabilities->can_generate_garbage_collection_events = 1;

	if (returnCode != JNI_OK)
	{
		fprintf(stderr, "C:\tJVM does not have the required capabilities (%d)\n",
				returnCode);
		exit(-1);
	}



	returnCode = (*jvmti_env)->AddCapabilities(jvmti_env, requiredCapabilities);


	jvmtiEventCallbacks *eventCallbacks;

	eventCallbacks = calloc(1, sizeof(jvmtiEventCallbacks));
	if (!eventCallbacks)
	{
		fprintf(stderr, "Unable to allocate memory\n");
		return JVMTI_ERROR_OUT_OF_MEMORY;
	}

	eventCallbacks->GarbageCollectionStart = &garbageCollectionStart;
	eventCallbacks->GarbageCollectionFinish = &garbageCollectionFinish;


	returnCode = (*jvmti_env)->SetEventCallbacks(jvmti_env,
			eventCallbacks, (jint) sizeof(*eventCallbacks));


	if (returnCode != JNI_OK)
	{
		fprintf(stderr, "C:\tError setting event callbacks (%d)\n",
				returnCode);
		exit(-1);
	}

	returnCode = (*jvmti_env)->SetEventNotificationMode(
			jvmti_env, JVMTI_ENABLE, JVMTI_EVENT_GARBAGE_COLLECTION_START, (jthread) NULL);

	if (returnCode != JNI_OK)
	{
		fprintf(
				stderr,
				"C:\tJVM does not have the required capabilities, JVMTI_ENABLE, JVMTI_EVENT_GARBAGE_COLLECTION_START (%d)\n",
				returnCode);
		exit(-1);
	}


	returnCode = (*jvmti_env)->SetEventNotificationMode(
			jvmti_env, JVMTI_ENABLE, JVMTI_EVENT_GARBAGE_COLLECTION_FINISH, (jthread) NULL);

	if (returnCode != JNI_OK)
	{
		fprintf(
				stderr,
				"C:\tJVM does not have the required capabilities, JVMTI_ENABLE, JVMTI_EVENT_GARBAGE_COLLECTION_FINISH (%d)\n",
				returnCode);
		exit(-1);
	}


	if(requiredCapabilities) free(requiredCapabilities);
	if(eventCallbacks) free(eventCallbacks);

	remove(GC_TRACE_PATH);

	return JVMTI_ERROR_NONE;
}
