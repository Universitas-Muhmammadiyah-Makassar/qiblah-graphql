module.exports = {
    apps: [
      {
        name: "qiblah-graphql",    // Name of the app in PM2
        script: "uvicorn",         // Script to run (use uvicorn as the script)
        args: "app:app --reload --host 0.0.0.0 --port 8118", // Arguments to pass to uvicorn
        exec_mode: "cluster",      // Cluster mode for multi-node processes
        instances: 3,              // Number of instances (3 nodes)
        interpreter: "python3",    // Python interpreter to use
        watch: true,               // Enable watch mode (optional, for development)
        autorestart: true,         // Auto-restart if the app crashes
        max_memory_restart: "1G",  // Restart if memory usage exceeds 1GB
      }
    ]
  };