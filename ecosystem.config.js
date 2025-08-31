module.exports = {
  apps: [
    {
      name: 'taxsale-backend',
      script: 'server.py',
      interpreter: '/var/www/nstaxsales/backend/venv/bin/python',
      cwd: '/var/www/nstaxsales/backend',
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      }
    },
    {
      name: 'taxsale-frontend',
      script: '/usr/bin/serve',
      args: '-s build -p 3000',
      cwd: '/var/www/nstaxsales/frontend',
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      env: {
        NODE_ENV: 'production'
      }
    }
  ]
};
