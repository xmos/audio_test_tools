pipeline {
  agent {
    label 'x86&&macOS&&Apps'
  }
  environment {
    VIEW = 'hydra'
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
    stage('test_parse_wav_header') {
      steps {
        viewEnv() {
          dir("${REPO}/tests/test_parse_wav_header") {
            sh "xwaf configure build"
            sh "axe bin/test_wav.xe"
          }
        }
      }
    }
  }
  post {
    failure {
      slackSend(color: '#FF0000', channel: '#hydra', message: "Fail: ${currentBuild.fullDisplayName} (${env.RUN_DISPLAY_URL})")
    }
    cleanup {
      cleanWs()
    }
  }
}
