@Library('xmos_jenkins_shared_library@develop') _
pipeline {
  agent {
    label 'x86 && macOS && && brew'        
  }
  environment {
    VIEW = 'audio_test_tools_master'
    REPO = 'audio_test_tools'
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
            runXwaf('.')
            runPytest('1')
          }
        }
      }
    }
    stage('att_unit_tests') {
      steps {
        viewEnv() {
          dir("${REPO}/tests/att_unit_tests") {
              runXwaf('.')
              runPytest()
          }
        }
      }
    }
    stage('Build test_process_wav') {
      steps {
        viewEnv() {
          dir("${REPO}/tests/test_process_wav") {
              runXwaf('.')
          }
        }
      }
    }
  }
  post {
    success {
      updateViewfiles()
    }
    cleanup {
      cleanWs()
    }
  }
}
