@Library('jenkings') _

def buildImage(tag, arch, flavour) {
  imageName = "majorcadevs/mdbackup:${tag}"
  try {
    docker.image(imageName).pull()
  } catch(e) {}
  return docker.build(imageName, "--pull --build-arg ARCH=${arch} -f docker/Dockerfile-${flavour} .")
}

def pushImage(img, tag) {
  docker.withRegistry('https://registry.hub.docker.com', 'bobthabuilda') {
    img.push("${GIT_TAG}-${tag}")
    if(env.BRANCH_NAME == 'master') {
      img.push(tag)
    }
  }
}

pipeline {
  agent {
    label '!docker-qemu'
  }

  environment {
    CI = 'true'
    GIT_TAG = ''
    IS_DRAFT = false
  }

  stages {
    stage('Get git tag') {
      steps {
        script {
          GIT_TAG = sh(script: 'git tag -l --contains HEAD', returnStdout: true).trim()
          if(GIT_TAG == '') {
            GIT_TAG = null
            echo 'No tag detected'
          } else {
            IS_DRAFT = GIT_TAG.matches('v?\\d+\\.\\d+\\.\\d+-.+')
            echo "Tag detected: ${GIT_TAG} - is draft? ${IS_DRAFT}"
            if(env.BRANCH_NAME.matches('master|dev')) {
              echo 'A release will be published'
            }
          }
        }
      }
    }

    stage('Test') {
      agent {
        docker {
          label 'docker'
          image 'python:3.7-buster'
          args '-e HOME=$WORKSPACE -e PATH=$PATH:$WORKSPACE/.local/bin'
        }
      }

      steps {
        script {
          sh 'pip install --user -r docker/dev/requirements.dev.txt'
          sh 'flake8 mdbackup'
          sh 'flake8 tests'
          sh 'coverage run --source=mdbackup --branch -m xmlrunner discover -s tests -p \'*tests*.py\' -o tests/.report'
          sh 'coverage xml -o coverage_report.xml'
          sh 'PYTHONPATH=$PWD python -m mdbackup --help'
        }
      }

      post {
        always {
          junit 'tests/.report/**/*.xml'
          cobertura coberturaReportFile: 'coverage_report.xml'
        }
      }
    }

    stage('Build wheel') {
      when {
        branch 'master|dev'
      }

      agent {
        docker {
          label 'docker'
          image 'python:3.7-buster'
          args '-e HOME=$WORKSPACE -e PATH=$PATH:$WORKSPACE/.local/bin'
        }
      }

      steps {
        script {
          sh 'python setup.py bdist_wheel'
          archiveArtifacts artifacts: 'dist/mdbackup-*.whl', fingerprint: true
        }
      }
    }

    stage('Build images') {
      when {
        branch 'master|dev'
        expression {
          GIT_TAG != null && GIT_TAG != ''
        }
      }

      parallel {
        stage('amd64-alpine') {
          agent {
            label 'docker-qemu'
          }

          environment {
            img = ''
            arch = 'amd64'
            flavour = 'alpine'
            tag = 'amd64_alpine'
          }

          stages {
            stage('Checkout') {
              steps {
                checkoutRepo()
              }
            }

            stage('Build image') {
              steps {
                script {
                  img = buildImage(tag, arch, flavour)
                }
              }
            }

            stage('Push image') {
              steps {
                script {
                  pushImage(img, tag)
                }
              }
            }
          }
        }

        stage('amd64-slim') {
          agent {
            label 'docker-qemu'
          }

          environment {
            img = ''
            arch = 'amd64'
            flavour = 'slim'
            tag = 'amd64_slim'
          }

          stages {
            stage('Checkout') {
              steps {
                checkoutRepo()
              }
            }

            stage('Build image') {
              steps {
                script {
                  img = buildImage(tag, arch, flavour)
                }
              }
            }

            stage('Push image') {
              steps {
                script {
                  pushImage(img, tag)
                }
              }
            }
          }
        }

        stage('armv8-alpine') {
          agent {
            label 'docker-qemu'
          }

          environment {
            img = ''
            arch = 'arm64v8'
            flavour = 'alpine'
            tag = 'armv8_alpine'
          }

          stages {
            stage('Checkout') {
              steps {
                checkoutRepo()
              }
            }

            stage('Build image') {
              steps {
                script {
                  img = buildImage(tag, arch, flavour)
                }
              }
            }

            stage('Push image') {
              steps {
                script {
                  pushImage(img, tag)
                }
              }
            }
          }
        }

        stage('armv8-slim') {
          agent {
            label 'docker-qemu'
          }

          environment {
            img = ''
            arch = 'arm64v8'
            flavour = 'slim'
            tag = 'armv8_slim'
          }

          stages {
            stage('Checkout') {
              steps {
                checkoutRepo()
              }
            }

            stage('Build image') {
              steps {
                script {
                  img = buildImage(tag, arch, flavour)
                }
              }
            }

            stage('Push image') {
              steps {
                script {
                  pushImage(img, tag)
                }
              }
            }
          }
        }

        stage('armv7-alpine') {
          agent {
            label 'docker-qemu'
          }

          environment {
            img = ''
            arch = 'arm32v7'
            flavour = 'alpine'
            tag = 'armv7_alpine'
          }

          stages {
            stage('Checkout') {
              steps {
                checkoutRepo()
              }
            }

            stage('Build image') {
              steps {
                script {
                  img = buildImage(tag, arch, flavour)
                }
              }
            }

            stage('Push image') {
              steps {
                script {
                  pushImage(img, tag)
                }
              }
            }
          }
        }

        stage('armv7-slim') {
          agent {
            label 'docker-qemu'
          }

          environment {
            img = ''
            arch = 'arm32v7'
            flavour = 'slim'
            tag = 'armv7_slim'
          }

          stages {
            stage('Checkout') {
              steps {
                checkoutRepo()
              }
            }

            stage('Build image') {
              steps {
                script {
                  img = buildImage(tag, arch, flavour)
                }
              }
            }

            stage('Push image') {
              steps {
                script {
                  pushImage(img, tag)
                }
              }
            }
          }
        }
      }
    }

    stage('Update manifest') {
      when {
        branch 'master|dev'
        expression {
          GIT_TAG != null && GIT_TAG != ''
        }
      }

      agent {
        label 'docker-qemu'
      }

      steps {
        script {
          if(env.BRANCH_NAME == 'master') {
            sh 'docker manifest create majorcadevs/mdbackup:slim majorcadevs/mdbackup:amd64_slim majorcadevs/mdbackup:armv7_slim majorcadevs/mdbackup:armv8_slim'
            sh 'docker manifest create majorcadevs/mdbackup:alpine majorcadevs/mdbackup:amd64_alpine majorcadevs/mdbackup:armv7_alpine majorcadevs/mdbackup:armv8_alpine'
          }
          sh "docker manifest create majorcadevs/mdbackup:${GIT_TAG}-slim majorcadevs/mdbackup:${GIT_TAG}-amd64_slim majorcadevs/mdbackup:${GIT_TAG}-armv7_slim majorcadevs/mdbackup:${GIT_TAG}-armv8_slim"
          sh "docker manifest create majorcadevs/mdbackup:${GIT_TAG}-alpine majorcadevs/mdbackup:${GIT_TAG}-amd64_alpine majorcadevs/mdbackup:${GIT_TAG}-armv7_alpine majorcadevs/mdbackup:${GIT_TAG}-armv8_alpine"
          docker.withRegistry('https://registry.hub.docker.com', 'bobthabuilda') {
            if(env.BRANCH_NAME == 'master') {
              sh 'docker manifest push -p majorcadevs/mdbackup:slim'
              sh 'docker manifest push -p majorcadevs/mdbackup:alpine'
            }
            sh "docker manifest push -p majorcadevs/mdbackup:${GIT_TAG}-slim"
            sh "docker manifest push -p majorcadevs/mdbackup:${GIT_TAG}-alpine"
          }
        }
      }
    }

    stage('Create release') {
      when {
        branch 'master|dev'
        expression {
          GIT_TAG != null && GIT_TAG != ''
        }
      }

      agent {
        label 'majorcadevs'
      }

      steps {
        script {
          unarchive mapping: ['dist/*.whl': '.']
          def file = sh(script: 'ls *.whl', returnStdout: true).trim()
          githubRelease(
            'amgxv-github-token',
            'majorcadevs/mdbackup',
            "${GIT_TAG}",
            "Release ${GIT_TAG}",
            "TBD",
            [
              [file, 'application/octet-stream'],
            ],
            draft: IS_DRAFT
          )
        }
      }
    }
  }
}
