require('dotenv').config();  // Load .env variables

module.exports = {
  apps: [
    {
      name: "qiblah-graphql",    
      script: "uvicorn",         
      args: `app:app --reload --host 0.0.0.0 --port ${process.env.PORT}`,  // Use the port from .env
      exec_mode: "cluster",      
      instances: 3,              
      interpreter: "python3",    
      watch: true,               
      autorestart: true,         
      max_memory_restart: "1G",  
    }
  ]
};