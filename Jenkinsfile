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
        // VIEW = getViewName(REPO)
        // VIEW = "${env.JOB_NAME.contains('PR-') ? REPO+'_'+env.CHANGE_TARGET : REPO+'_'+env.BRANCH_NAME}"
        VIEW = "audio_test_tools_feature_test_xs3"
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
              }
            }
          }
        }
        stage('Build test_process_wav') {
          steps {
            viewEnv() {
              dir("${REPO}/tests/test_process_wav") {
                  runWaf('.')
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
            toolsEnv(TOOLS_PATH) {  // load xmos tools
              unstash 'AN00162'
              sh 'xrun --id 0 bin/XCORE_AI/AN00162_i2s_loopback_demo.xe'

              //Just run on HW and error on incorrect binary etc. It will not run otherwise due to lack of loopback (intended for sim)
              //We run xsim afterwards for actual test (with loopback)
              // unstash 'backpressure_test'
              // sh 'xrun --id 0 bin/XCORE_AI/backpressure_test_XCORE_AI.xe'
              // sh 'xsim --xscope "-offline xscope.xmt" bin/XCORE_AI/backpressure_test_XCORE_AI.xe --plugin LoopbackPort.dll "-port tile[0] XS1_PORT_1G 1 0 -port tile[0] XS1_PORT_1A 1 0" > bp_test.txt'
              // sh 'cat bp_test.txt && diff bp_test.txt tests/backpressure_test.expect'
            }
          }
        }
      }//stages
      post {
        cleanup {
          cleanWs()
        }
      }
    }// xcore.ai
  }
}
