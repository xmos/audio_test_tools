pipeline {
  agent {
    label 'x86&&macOS&&Apps'
  }
  environment {
    VIEW = 'audio_test_tools_develop'
    REPO = 'audio_test_tools'
  }
  options {
    skipDefaultCheckout()
  }
  stages {
    stage('Get view') {
      steps {
        prepareAppsSandbox("${VIEW}", "${REPO}")
      }
    }
    stage('SW reference checks') {
      steps {
        xcoreSwrefChecks("${REPO}")
      }
    }
    stage('test_parse_wav_header') {
      steps {
        viewEnv() {
          dir("${REPO}/tests/test_parse_wav_header") {
            sh "xwaf configure build"
            withEnv(["PATH+PYDIR=/usr/local/bin"]) {
              // Continue to next stage if a test fails, the test is set as failure at the end
              sh "python -m pytest test_wav.py"
            }
          }
        }
      }
    }
    stage('att_unit_tests') {
      steps {
        viewEnv() {
          dir("${REPO}/tests/att_unit_tests") {
            withEnv(["PATH+PYDIR=/usr/local/bin"]) {
              sh "xwaf configure build test"
            }
          }
        }
      }
    }
    stage('Build test_process_wav') {
      steps {
        viewEnv() {
          dir("${REPO}/tests/test_process_wav") {
            withEnv(["PATH+PYDIR=/usr/local/bin"]) {
              sh "xwaf configure build"
            }
          }
        }
      }
    }
  }
  post {
    success {
      updateViewfiles()
    }
    failure {
      slackSend(color: '#FF0000', channel: '#hydra', message: "Fail: ${currentBuild.fullDisplayName} (${env.RUN_DISPLAY_URL})")
    }
    cleanup {
      cleanWs()
    }
  }
}
