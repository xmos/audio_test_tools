@Library('xmos_jenkins_shared_library@v0.16.2') _

getApproval()

pipeline {
  agent none

  environment {
    REPO = 'audio_test_tools'
    VIEW = getViewName(REPO)
  }

  stages {
    stage('Standard build and XS2 tests') {
      agent {
        label 'x86_64&&brew&&macOS'
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
        stage('Build docs') {
          steps {
            runXdoc("${REPO}/${REPO}/doc")
            // Archive all the generated .pdf docs
            archiveArtifacts artifacts: "${REPO}/**/pdf/*.pdf", fingerprint: true, allowEmptyArchive: true
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
        label 'xcore.ai'
      }
      options {
        skipDefaultCheckout()
      }
      stages{
        stage('Get View') {
            steps {
                xcorePrepareSandbox("${VIEW}", "${REPO}")
            }
        }        
        stage('Reset XTAGs'){
          steps{
            dir("${REPO}") {
              sh 'rm -f ~/.xtag/acquired' //Hacky but ensure it always works even when previous failed run left lock file present
              viewEnv() {
                withVenv{
                  sh "python -m pip install -e ${WORKSPACE}/xtagctl"
                  sh "xtagctl reset_all XCORE-AI-EXPLORER" 
                }
              }
            }
          }
        }        
        stage('xrun'){
          steps{
            dir("${REPO}") {
              viewEnv() {
                withVenv() {
                  dir("tests/test_parse_wav_header") {  // load xmos tools
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
        }
        stage('test_xscope_process_wav'){
          steps{
            dir("${REPO}") {
              viewEnv() {
                withVenv() {
                  dir("tests/test_xscope_process_wav") {  // load xmos tools
                    sh "pip install -e ${env.WORKSPACE}/xscope_fileio"                
                      unstash 'test_xscope_process_wav'
                      runPytest('-s --numprocesses=1')
                  }
                }
              }
            }
          }
        }
      }
      post {
        cleanup {
          cleanWs()
        }
      }
    }// xcore.ai
    stage('Update view files') {
      agent {
        label 'x86_64&&brew'
      }
      when {
        expression { return currentBuild.currentResult == "SUCCESS" }
      }
      steps {
        updateViewfiles()
      }
    }
  }
}
