// Powered by Infostretch 

timestamps {

node ('master') { 
	
	// Clean up workspace on entry
	stage ('shared_scripting_docs - Clean workspace') {
		deleteDir()
	}

	stage ('shared_scripting_docs - Checkout') {
 	 checkout([$class: 'GitSCM', branches: [[name: '*/Ticket3082_Shared_scripting_docs']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '6b2f1ee9-91ff-4bc5-ab7d-6a3282eb73b4', url: 'https://github.com/ISISNeutronMuon/InstrumentScripts']]]) 
	}
	stage ('shared_scripting_docs - Build') {
 			// Shell build step
sh """ 
cd docs
sh make_doc.sh 
 """
		archiveArtifacts allowEmptyArchive: false, artifacts: 'docs/_build/html/**/*', caseSensitive: true, defaultExcludes: true, fingerprint: false, onlyIfSuccessful: false 
	}
}
}
