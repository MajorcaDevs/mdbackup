@Library('jenkings') _

def generateImageName(arch, flavour) {
  return "majorcadevs/mdbackup:${GIT_TAG}-${arch}-${flavour}"
}

def buildImage(arch, flavour) {
  def imageName = generateImageName(arch, flavour)
  try {
    docker.image(imageName).pull()
  } catch(e) {}
  docker.build(imageName, "--pull --build-arg ARCH=${arch} -f docker/Dockerfile-${flavour} .")
}

def pushImage(arch, flavour) {
  docker.withRegistry('https://registry.hub.docker.com', 'bobthabuilda') {
    def imageName = generateImageName(arch, flavour)
    def img = docker.image(imageName)
    img.push("${GIT_TAG}-${arch}-${flavour}")
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
          sh 'pip install --user -r docker/requirements.txt'
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
        expression {
          BRANCH_NAME ==~ /master|dev/
        }
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
          dir('dist') {
            archiveArtifacts artifacts: 'mdbackup-*.whl', fingerprint: true
          }
        }
      }
    }

    stage('Build docs') {
      when {
        expression {
          BRANCH_NAME ==~ /master|dev/
        }
      }

      agent {
        dockerfile {
          label 'docker'
          filename 'docs/docker/Dockerfile.jenkins'
          args '-e HOME=$WORKSPACE -e PATH=$PATH:$WORKSPACE/.local/bin'
        }
      }

      environment {
        HOMEPAGE_URL = 'https://mdbackup.majorcadevs.com/'
      }

      steps {
        script {
          sh './docs/docker/versioning-build.sh'
          if(env.HOMEPAGE_URL.indexOf('github.io') == -1) {
            def domain = (env.HOMEPAGE_URL =~ /^https?:\/\/([^\/]+)/)[0][1]
            sh "echo ${domain} > build/docs/CNAME"
          }

          withCredentials([
            usernamePassword(credentialsId: 'GitHub-melchor629',
                             usernameVariable: 'GIT_USERNAME',
                             passwordVariable: 'GIT_PASSWORD')
          ]) {
            sh 'git config user.name "melchor629"'
            sh 'git config user.email "melchor9000@gmail.com"'
            sh 'git remote set-url origin https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/MajorcaDevs/mdbackup'
            sh 'npx gh-pages -d build/docs'
          }
        }
      }
    }

    stage('Build images') {
      when {
        expression {
          GIT_TAG != null && GIT_TAG != '' && BRANCH_NAME ==~ /master|dev/
        }
      }

      parallel {
        stage('amd64-alpine') {
          agent {
            label 'docker-qemu'
          }

          environment {
            arch = 'amd64'
            flavour = 'alpine'
          }

          stages {
            stage('Build image') {
              steps {
                script {
                  buildImage(arch, flavour)
                }
              }
            }

            stage('Push image') {
              steps {
                script {
                  pushImage(arch, flavour)
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
            arch = 'amd64'
            flavour = 'slim'
          }

          stages {
            stage('Build image') {
              steps {
                script {
                  buildImage(arch, flavour)
                }
              }
            }

            stage('Push image') {
              steps {
                script {
                  pushImage(arch, flavour)
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
            arch = 'arm64v8'
            flavour = 'alpine'
          }

          stages {
            stage('Build image') {
              steps {
                script {
                  buildImage(arch, flavour)
                }
              }
            }

            stage('Push image') {
              steps {
                script {
                  pushImage(arch, flavour)
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
            arch = 'arm64v8'
            flavour = 'slim'
          }

          stages {
            stage('Build image') {
              steps {
                script {
                  buildImage(arch, flavour)
                }
              }
            }

            stage('Push image') {
              steps {
                script {
                  pushImage(arch, flavour)
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
            arch = 'arm32v7'
            flavour = 'alpine'
          }

          stages {
            stage('Build image') {
              steps {
                script {
                  buildImage(arch, flavour)
                }
              }
            }

            stage('Push image') {
              steps {
                script {
                  pushImage(arch, flavour)
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
            arch = 'arm32v7'
            flavour = 'slim'
          }

          stages {
            stage('Build image') {
              steps {
                script {
                  buildImage(arch, flavour)
                }
              }
            }

            stage('Push image') {
              steps {
                script {
                  pushImage(arch, flavour)
                }
              }
            }
          }
        }
      }
    }

    stage('Update manifest') {
      when {
        expression {
          GIT_TAG != null && GIT_TAG != '' && BRANCH_NAME ==~ /master|dev/
        }
      }

      agent {
        label 'docker-qemu'
      }

      steps {
        script {
          def flavours = ['slim', 'alpine']
          def arches = ['amd64', 'arm32v7', 'arm64v8']
          def images = [:]

          flavours.each { flavour ->
            images[flavour] = arches
              .collect { arch -> generateImageName(arch, flavour) }
              .join(' ')
          }

          images.each { flavour, imgs ->
            docker.withRegistry('', 'bobthabuilda') {
              sh "docker manifest create majorcadevs/mdbackup:${GIT_TAG}-${flavour} ${imgs}"
              sh "docker manifest push -p majorcadevs/mdbackup:${GIT_TAG}-${flavour}"
              if(env.BRANCH_NAME == 'master') {
                sh "docker manifest create majorcadevs/mdbackup:${flavour} ${imgs}"
                sh "docker manifest push -p majorcadevs/mdbackup:${flavour}"
              }
            }
          }
        }
      }
    }

    stage('Create release') {
      when {
        expression {
          GIT_TAG != null && GIT_TAG != '' && BRANCH_NAME ==~ /master|dev/
        }
      }

      agent {
        label 'majorcadevs'
      }

      steps {
        script {
          unarchive mapping: ['*.whl': '.']
          def file = sh(script: 'ls *.whl', returnStdout: true).trim()
          githubRelease(
            'amgxv-github-token',
            'majorcadevs/mdbackup',
            "${GIT_TAG}".toString(),
            "Release ${GIT_TAG}".toString(),
            'TBD',
            [
              [file, 'application/octet-stream'],
            ],
            IS_DRAFT && IS_DRAFT == 'true'
          )
        }
      }
    }
  }
}
