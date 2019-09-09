@Library('xmos_jenkins_shared_library@develop') _

getApproval()

pipeline {
  agent {
    label 'x86_64 && brew'
  }
  environment {
    REPO = 'audio_test_tools'
    VIEW = 'audio_test_tools_xwaf_xcommon'
    //VIEW = "${env.JOB_NAME.contains('PR-') ? REPO+'_'+env.CHANGE_TARGET : REPO+'_'+env.BRANCH_NAME}"
  }
  options {
    skipDefaultCheckout()
  }
  triggers {
    /* Trigger this Pipeline on changes to the repos dependencies
     *
     * If this Pipeline is running in a pull request, the triggers are set
     * on the base branch the PR is set to merge in to.
     *
     * Otherwise the triggers are set on the branch of a matching name to the
     * one this Pipeline is on.
     */
    upstream(
      upstreamProjects:
        (env.JOB_NAME.contains('PR-') ?
          "../lib_dsp/${env.CHANGE_TARGET}," +
          "../lib_voice_toolbox/${env.CHANGE_TARGET}," +
          "../tools_released/${env.CHANGE_TARGET}," +
          "../tools_xmostest/${env.CHANGE_TARGET}," +
          "../xdoc_released/${env.CHANGE_TARGET}"
        :
          "../lib_dsp/${env.BRANCH_NAME}," +
          "../lib_voice_toolbox/${env.BRANCH_NAME}," +
          "../tools_released/${env.BRANCH_NAME}," +
          "../tools_xmostest/${env.BRANCH_NAME}," +
          "../xdoc_released/${env.BRANCH_NAME}"),
      threshold: hudson.model.Result.SUCCESS
    )
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
      xcoreCleanSandbox()
    }
  }
}
