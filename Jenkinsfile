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
    img.push(tag)
  }
}

pipeline {
  agent {
    label '!docker-qemu'
  }

  environment {
    CI = 'true'
  }

  stages {
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
    }

    stage('Build images') {
      when {
        branch 'master'
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
        branch 'master'
      }

      agent {
        label 'docker-qemu'
      }

      steps {
        script {
          sh 'docker manifest create majorcadevs/mdbackup:slim majorcadevs/mdbackup:amd64_slim majorcadevs/mdbackup:armv7_slim majorcadevs/mdbackup:armv8_slim'
          sh 'docker manifest create majorcadevs/mdbackup:alpine majorcadevs/mdbackup:amd64_alpine majorcadevs/mdbackup:armv7_alpine majorcadevs/mdbackup:armv8_alpine'
          docker.withRegistry('https://registry.hub.docker.com', 'bobthabuilda') {
            sh 'docker manifest push -p majorcadevs/mdbackup:slim'
            sh 'docker manifest push -p majorcadevs/mdbackup:alpine'
          }
        }
      }
    }
  }

  post {
    always {
      junit 'tests/.report/**/*.xml'
      cobertura coberturaReportFile: 'coverage_report.xml'
    }
  }
}
