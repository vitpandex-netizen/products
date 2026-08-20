module.exports = {
  apps: [
    {
      name: 'finanalytics-bot',
      script: 'src/main.py',
      args: '--bot',
      cwd: __dirname,
      interpreter: __dirname + '/venv/bin/python3',
      env: { PYTHONPATH: __dirname + '/src', LOG_LEVEL: 'INFO' },
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: 'logs/pm2-error.log', out_file: 'logs/pm2-out.log',
      max_restarts: 10, restart_delay: 5000, autorestart: true,
    },
    {
      name: 'finanalytics-dashboard',
      script: 'src/main.py',
      args: '--serve',
      cwd: __dirname,
      interpreter: __dirname + '/venv/bin/python3',
      env: { PYTHONPATH: __dirname + '/src', LOG_LEVEL: 'INFO' },
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: 'logs/dash-error.log', out_file: 'logs/dash-out.log',
      max_restarts: 10, restart_delay: 5000, autorestart: true,
    }
  ]
};
