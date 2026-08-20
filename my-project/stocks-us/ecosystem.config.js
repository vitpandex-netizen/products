module.exports = {
  apps: [{
    name: 'stocks-us-bot',
    script: 'src/main.py',
    args: '--bot',
    cwd: __dirname,
    interpreter: '/Volumes/External/dev/my-project/stocks-us/venv/bin/python3',
    env: {
      PYTHONPATH: __dirname + '/src',
      LOG_LEVEL: 'INFO',
    },
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    error_file: 'logs/pm2-error.log',
    out_file: 'logs/pm2-out.log',
    merge_logs: true,
    max_restarts: 10,
    restart_delay: 5000,
    autorestart: true,
  }]
};
