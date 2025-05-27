pipeline {

    agent any
    
    parameters {
        booleanParam(
            name: 'FULL_CLEANUP',
            defaultValue: false,
            description: 'Perform full Docker system cleanup (slower but frees more space)'
        )
    }

    environment {
        PATH = "$PATH:/usr/local/bin:/usr/bin:/bin:$HOME/miniforge3/bin:$HOME/miniforge3/condabin"

        // Enabling Docker BuildKit for faster builds and caching
        DOCKER_BUILDKIT = '1'
        COMPOSE_DOCKER_CLI_BUILD = '1'

        // Setting environment variables for MinIO (set in Jenkins credentials)
        MINIO_ENDPOINT = credentials('MINIO_ENDPOINT')
        MINIO_ACCESS_KEY = credentials('MINIO_ACCESS_KEY')
        MINIO_SECRET_KEY = credentials('MINIO_SECRET_KEY')
        MINIO_SECURE = credentials('MINIO_SECURE')
        MINIO_BUCKET = credentials('MINIO_BUCKET')

        // Setting environment variables for Snowflake (set in Jenkins credentials)
        SNOWFLAKE_USER = credentials('SNOWFLAKE_USER')
        SNOWFLAKE_ACCOUNT = credentials('SNOWFLAKE_ACCOUNT')
        SNOWFLAKE_WAREHOUSE = credentials('SNOWFLAKE_WAREHOUSE')
        SNOWFLAKE_DATABASE = credentials('SNOWFLAKE_DATABASE')
        SNOWFLAKE_SCHEMA = credentials('SNOWFLAKE_SCHEMA')
        SNOWFLAKE_ROLE = credentials('SNOWFLAKE_ROLE')
    }

    stages {
        stage('Checkout') {
            steps {
                // Using local repo and update it
                sh '''
                    cd /home/jenkins/BenBox
                    git pull origin main
                '''
            }
        }

        stage('Test (Pytest)') {
            steps {
                sh '''
                    cd /home/jenkins/BenBox
                    $HOME/miniforge3/condabin/conda run -n BenBox python -m pytest --maxfail=1 --disable-warnings --junitxml=test.xml
                    cp /home/jenkins/BenBox/test.xml $WORKSPACE/test.xml
                '''
            }
            post {
                always {
                    // Publishing PyTest JUnit XML results from workspace
                    junit 'test.xml'
                }
            }
        }

        stage('Build & Deploy') {
            steps {
                // Using local repo and building docker image and deploying
                sh '''
                    cd /home/jenkins/BenBox
                    
                    # Stopping current containers with build-specific project name
                    docker stop benbox streamlit mcp
                    docker rm benbox streamlit mcp
                    docker-compose -f docker-compose.yml --project-name benbox-${BUILD_NUMBER} down --remove-orphans

                    # Smart cleanup - only removing build-specific artifacts and dangling images
                    docker container prune -f --filter "until=1h"
                    docker image prune -f

                    # Building with cache support (no --no-cache for faster builds)
                    docker-compose -f docker-compose.yml --project-name benbox-${BUILD_NUMBER} build

                    # Deploying with build-specific project name
                    docker-compose -f docker-compose.yml --project-name benbox-${BUILD_NUMBER} up -d
                '''
            }
        }

        stage('Full Cleanup') {
            when {
                anyOf {
                    // Only full cleanup on scheduled builds or when manually triggered
                    triggeredBy 'TimerTrigger'
                    expression { params.FULL_CLEANUP == true }
                }
            }
            steps {
                sh '''
                    cd /home/jenkins/BenBox
                    # Full system cleanup only when needed
                    docker system prune -af --volumes
                    docker volume prune -f
                '''
            }
        }
    }
    
    post {
        always {
            script {
                // Cleaning up build-specific containers after build completion
                sh '''
                    # Removing any dangling images created during this build
                    docker image prune -f || true
                '''
            }
        }

        success {
            echo 'Build completed successfully!'
        }

        failure {
            echo 'Build failed. Check logs for details.'
        }
    }
}
