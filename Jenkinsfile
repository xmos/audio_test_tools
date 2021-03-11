@Library('xmos_jenkins_shared_library@v0.15.1') _

getApproval()

pipeline {
  agent none
  //Tools for AI verif stage. Tools for standard stage in view file
  parameters {
    string(
      name: 'TOOLS_VERSION',
      defaultValue: '15.0.2',
      description: 'The tools version to build with (check /projects/tools/ReleasesTools/)'
      )
  }
  stages {
    stage('Standard build and XS2 tests') {
      agent {
        label 'x86_64 && brew'
      }
      environment {
        REPO = 'audio_test_tools'
         VIEW = getViewName(REPO)
      }
      options {
        skipDefaultCheckout()
      }
      stages {
        stage('Get view') {
          steps {
            xcorePrepareSandbox("${VIEW}", "${REPO}")

          }
        }
        stage('SW reference checks (NOT ALL)') {
          parallel {
            stage ("Flake 8") {
              steps {
                viewEnv() {
                  flake("${REPO}")
                }
              }
            }
            stage ("Copyright") {
              steps {
                viewEnv() {
                  sourceCheck("${REPO}")
                }
              }
            }
            stage ("Changelog (NOT IMPLEMENTED)") {
              steps {
                viewEnv() {
                  echo "TODO: Add full Swref checks: Requires fix for #86"
                }
              }
            }
            stage ("Clang style") {
              steps {
                viewEnv() {
                  clangStyleCheck()
                }
              }
            }
          }
        }
        stage('test_parse_wav_header') {
          steps {
            viewEnv() {
              dir("${REPO}/tests/test_parse_wav_header") {
                runXmake(".", "", "XCOREAI=0")
                runPytest('--numprocesses=1')
                runXmake(".", "", "XCOREAI=1")
                stash name: 'test_parse_wav_header', includes: 'bin/AI/test_wav_parse_header.xe, '
              }
            }
          }
        }
        stage('att_unit_tests') {
          steps {
            viewEnv() {
              dir("${REPO}/tests/att_unit_tests") {
                  runWaf('.', "configure clean build")
                  runPytest()
                  runWaf('.', "configure clean build --ai")
                  sh 'tree'
                  stash name: 'att_unit_tests', includes: 'bin/test_limit_bits.xe, '
              }
            }
          }
        }
        stage('Build test_process_wav') {
          steps {
            viewEnv() {
              dir("${REPO}/tests/test_process_wav") {
                runXmake(".", "", "XCOREAI=0")
                runXmake(".", "", "XCOREAI=1")
              }
            }
          }
        }
        stage('Build test_xscope_process_wav') {
          steps {
            viewEnv() {
              dir("${REPO}/tests/test_xscope_process_wav") {
                runWaf('.', "configure clean build")
                stash name: 'test_xscope_process_wav', includes: 'bin/test_xscope_process_wav.xe, '
              }
            }
          }
        }
      }//stages
      post {
        cleanup {
          xcoreCleanSandbox()
        }
      }
    }//Standard build and XS2 tests

    stage('xcore.ai Verification'){
      agent {
        label 'xcore.ai-explorer'
      }
      environment {
        // '/XMOS/tools' from get_tools.py and rest from tools installers
        TOOLS_PATH = "/XMOS/tools/${params.TOOLS_VERSION}/XMOS/xTIMEcomposer/${params.TOOLS_VERSION}"
      }
      stages{
        stage('Install Dependencies') {
          steps {
            sh '/XMOS/get_tools.py ' + params.TOOLS_VERSION
            installDependencies()
          }
        }
        stage('xrun'){
          steps{
            withVenv() {
              toolsEnv(TOOLS_PATH) {  // load xmos tools
                dir("tests/test_parse_wav_header") {
                  unstash 'test_parse_wav_header'
                  sh 'python test_wav.py --ai' //Note using pytest as we are passing an argument
                }
                dir("tests/att_unit_tests") {
                  unstash 'att_unit_tests'
                  sh 'xrun --io --id 0 bin/test_limit_bits.xe'
                }
              }
            }
          }
        }
        stage('test_xscope_process_wav'){
          steps{
            withVenv() {
              toolsEnv(TOOLS_PATH) {  // load xmos tools
                dir("audio_test_tools/host"){
                  sh 'make'
                }
                dir("tests/test_xscope_process_wav") {
                  unstash 'test_xscope_process_wav'
                  runPytest('-s --numprocesses=1')
                }
              }
            }
          }
        }
      }//stages
      post {
        success {
          updateViewfiles()
        }
        cleanup {
          cleanWs()
        }
      }
    }// xcore.ai
  }
}
