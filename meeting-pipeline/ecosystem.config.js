module.exports = {
  apps: [
    {
      name: "meeting-pipeline",
      cwd: "/Volumes/External/dev/meeting-pipeline",
      script: "python3",
      args: "meeting_service.py",
      env: {
        MEETING_SERVICE_PORT: "8001",
        TRANSCRIBE_SERVICE_URL: "http://transcribe-service:8000"
      },
      max_restarts: 10,
      restart_delay: 5000,
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      error_file: "/tmp/meeting-pipeline-error.log",
      out_file: "/tmp/meeting-pipeline-out.log"
    },
    {
      name: "meeting-watch",
      cwd: "/Volumes/External/dev/meeting-pipeline",
      script: "python3",
      args: "watch_service.py --dir /Volumes/External/recordings/ --service http://localhost:8001",
      max_restarts: 10,
      restart_delay: 5000,
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      error_file: "/tmp/meeting-watch-error.log",
      out_file: "/tmp/meeting-watch-out.log"
    }
  ]
};
